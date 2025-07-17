from sympy import randprime
from math import ceil as round_up
import secrets
from HashAlgorithm import SHA1
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os


class RSA:
    def __init__(self, key_length=2048):
        # e is fixed at 65537 for security
        self.__e = 65537
        self.__key_length = key_length
        # Specify bit size each of the primes
        bit_size = self.__key_length // 2
        self.__p, self.__q = self.__generate_primes(bit_size)
        self.__n = self.__p * self.__q
        self.__totient_n = self.__eulers_totient(self.__p, self.__q)

        # Ensure e is valid and bit length is correct
        while not self.__check_e_validity(self.__e, self.__totient_n) or self.__n.bit_length() < self.__key_length:
            # Keep generating p and q until it works with e value
            self.__p, self.__q = self.__generate_primes(bit_size)
            self.__n = self.__p * self.__q
            self.__totient_n = self.__eulers_totient(self.__p, self.__q)

        # Compute modular inverse (private key exponent d)
        # Dont need the other coefficient so _ to ignore it nor do we need gcd
        _, self.__d, _ = self.__find_gcd(self.__e, self.__totient_n, extended=True)

        # Ensure d is positive
        if self.__d < 0:
            self.__d += self.__totient_n

        # Set the key values
        self.public_key = (self.__e, self.__n)
        self.private_key = (self.__d, self.__n)


    def __generate_primes(self, bit_size):
        #Generate two distinct prime numbers of given bit size
        lower_bound, upper_bound = 2**(bit_size - 1), 2**bit_size - 1
        p, q = randprime(lower_bound, upper_bound), randprime(lower_bound, upper_bound)
        # Ensure they are not the same prime
        while p == q:
            q = randprime(lower_bound, upper_bound)
        return p, q

    def __eulers_totient(self, p, q):
        return (p - 1) * (q - 1)

    def __check_e_validity(self, e, totient_n):
        #Ensure e is co-prime with totient_n
        return 1 < e < totient_n and self.__find_gcd(e, totient_n) == 1

    def __find_gcd(self, a, b, extended=False):
        #Find the greatest common divisor (GCD) using the extended Euclidean algorithm
        # Returns data: (gcd, y , x)
        # Set base case
        if a == 0:
            if extended:
                return (b,0,1)
            else:
                return b
        # Recursion until base case
        gcd, x, y = self.__find_gcd(b % a, a, extended=True)
        return (gcd, y - (b // a) * x, x) if extended else gcd

    def __xor_bytes(self, byte1, byte2):
        #Perform XOR operation on two byte arrays
        if len(byte1) != len(byte2):
            raise ValueError("Byte arrays must be of the same length.")
        return bytes(b1 ^ b2 for b1, b2 in zip(byte1, byte2))

    def __padding_scheme(self, message):
        if isinstance(message, str):
            # Convert string to bytes
            message = message.encode("utf-8") 

        seed_length = 20  # SHA-1 produces 20-byte hashes
        seed = secrets.token_bytes(seed_length)  # Generate a random seed
        bytes_available = (self.__key_length // 8) - 1 # Subtract 1 to prevent an anomoly with exponential calculation in decrypt and encrypt
        # FORMAT: SEED|DATABLOCK
        datablock_length = bytes_available - seed_length

        # Create padding
        padding_required = datablock_length - 1 - len(message) # subtract 1 for the delimiter
        padding = b"\x00" * padding_required + b"\x01"  # Padding + delimiter

        # Masking process
        datablock = padding + message
        datablock_mask = self.__mask_generation(seed, datablock_length)
        masked_datablock = self.__xor_bytes(datablock, datablock_mask)
        seed_mask = self.__mask_generation(masked_datablock, seed_length)
        masked_seed = self.__xor_bytes(seed, seed_mask)

        # Make sure it's in big endian
        return int.from_bytes(masked_seed + masked_datablock, "big")

    def __mask_generation(self, value, mask_len):
        #Generate a mask using the SHA-1 algorithm
        sha1 = SHA1()
        blocks = round_up(mask_len / 20)
        mask = b""
        # More blocks the more iterations and bigger the mask will be 
        for i in range(blocks):
            counter = i.to_bytes(4, "big")
            mask += bytes.fromhex(sha1.hash(value + counter, hex=True))
        
        # Truncate it to fit the required mask length
        return mask[:mask_len]

    def encrypt(self, message, public_key):
        e, n = public_key
        encoded_message = self.__padding_scheme(message)
        # Perform encoded_message^e % n
        return pow(encoded_message, e, n)

    def decrypt(self, ciphertext):
        d, n = self.private_key
        # Perform ciphertext^d % n
        message_integer = pow(ciphertext, d, n)
        # Convert integer to big endian bytes
        encoded_message = message_integer.to_bytes((message_integer.bit_length() + 7) // 8, "big")

        # Extract masked seed and masked datablock
        seed_length = 20
        masked_seed, masked_datablock = encoded_message[:seed_length], encoded_message[seed_length:]

        # Undo mask generation
        seed_mask = self.__mask_generation(masked_datablock, seed_length)
        seed = self.__xor_bytes(masked_seed, seed_mask)
        datablock_mask = self.__mask_generation(seed, len(masked_datablock))
        datablock = self.__xor_bytes(masked_datablock, datablock_mask)

        # Extract message
        # Find the delimiter byte
        index = datablock.find(b"\x01")
        if index != -1:
            return datablock[index + 1:]
        raise ValueError("Delimiter byte (0x01) not found in decrypted datablock.")


class AES:
    def __init__(self, key):
        if isinstance(key, str):
            key = key.encode()  
        if len(key) != 32:
            raise ValueError("AES key must be exactly 32 bytes (256 bits).")
        
        self.__key = key
        self.__block_size = 128  # AES block size in bits

    def encrypt(self, plaintext):
        # Encrypts data using AES-256-CBC. The input plaintext must be   B64 encoded
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')  # Convert string to bytes
        
    
        # PKCS7 Padding
        padder = padding.PKCS7(self.__block_size).padder()
        padded_data = padder.update(plaintext) + padder.finalize()

        # Generate a random 16-byte IV
        iv = os.urandom(16)

        # AES-CBC Encryption
        cipher = Cipher(algorithms.AES(self.__key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        encrypted_message = iv + ciphertext
        return encrypted_message

    def decrypt(self, encrypted_data):
        # Decrypts AES-256-CBC encrypted data. Output is plaintext
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode('utf-8')  # Ensure it's bytes

        
        # Extract IV and ciphertext
        iv, ciphertext = encrypted_data[:16], encrypted_data[16:]

        # AES-CBC Decryption
        cipher = Cipher(algorithms.AES(self.__key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove PKCS7 Padding
        unpadder = padding.PKCS7(self.__block_size).unpadder()
        unpadded_data = unpadder.update(padded_data) + unpadder.finalize()

        return unpadded_data