

class SHA1():
    def __init__(self):
        # Initialize Hash Constants
        # Used agreed upon hash constants
        self.__H0 = 0x67452301
        self.__H1 = 0xEFCDAB89
        self.__H2 = 0x98BADCFE
        self.__H3 = 0x10325476
        self.__H4 = 0xC3D2E1F0

    def __rotate_left(self, value, shift):
        # Rotate integer x amount to left or right, and mask 
        return ((value << shift) | (value >> (32 - shift))) & 0xFFFFFFFF

    def __round_up_to_block(self, num):
        # Calculate the next multiple of 512
        next_multiple_of_512 = ((num + 511) // 512) * 512
        # Return 64 bits short of the nearest greatest 512 bits. 64 bits is for the binary rep of the length of message
        if (num % 512) < 448:
            return next_multiple_of_512 - 64
        else:
            return (next_multiple_of_512 + 512) - 64    

    def __return_plaintext_len(self, length):
        return format(length * 8, '064b')  # 64-bit representation of the length

    def hash(self, plaintext, hex=False):
        # Ensure plaintext is bytes before processing
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        # Split into 512-bit blocks
        binary_blocks = self.__initialize_input(plaintext)

        # Initialize hash registers
        h0, h1, h2, h3, h4 = self.__H0, self.__H1, self.__H2, self.__H3, self.__H4

        # Run main loop for each block
        for block in binary_blocks:
            # generate words for the block
            original_words = self.__partition_to_16_words(block)
            w = self.__partition_to_80_words(original_words)
            # Initialize working variables to the hash registers
            a, b, c, d, e = h0, h1, h2, h3, h4

            # Main loop
            for i in range(80):
                if i < 20:
                    f = (b & c) | (~b & d)
                    k = 0x5A827999
                elif i < 40:
                    f = b ^ c ^ d
                    k = 0x6ED9EBA1
                elif i < 60:
                    f = (b & c) | (b & d) | (c & d)
                    k = 0x8F1BBCDC
                else:
                    f = b ^ c ^ d
                    k = 0xCA62C1D6

                temp = (self.__rotate_left(a, 5) + f + e + w[i] + k) & 0xFFFFFFFF
                # Update working Variables for next interation
                e, d, c, b, a = d, c, self.__rotate_left(b, 30), a, temp
            # update hash registers -> become working variables for next block
            h0 = (h0 + a) & 0xFFFFFFFF
            h1 = (h1 + b) & 0xFFFFFFFF
            h2 = (h2 + c) & 0xFFFFFFFF
            h3 = (h3 + d) & 0xFFFFFFFF
            h4 = (h4 + e) & 0xFFFFFFFF
        # Create final hash by joining hash registers together
        final_hash_hex = ''.join(f'{x:08x}' for x in [h0, h1, h2, h3, h4])

        return final_hash_hex if hex else f"{h0}{h1}{h2}{h3}{h4}"

    def __partition_to_80_words(self, original_words):
        # Create list for all 80 words,even those that dont exist yet. [original words, 0, 0, 0]
        total_words = original_words + [0] * (80 - len(original_words))
        # Run calculation for new words after the orignal words 
        # new words after index 15
        for i in range(16, 80):
            # Calculation
            xor_result = total_words[i - 3] ^ total_words[i - 8] ^ total_words[i - 14] ^ total_words[i - 16]
            # Ensure to mask
            total_words[i] = self.__rotate_left(xor_result, 1) & 0xFFFFFFFF
        return total_words

    def __partition_to_512_blocks(self, bin_message):
        # Split entire binary message to blocks
        return [bin_message[i:i+512] for i in range(0, len(bin_message), 512)]

    def __partition_to_16_words(self, message):
        # Retrieve binary message and convert to integer words
        return [int(message[i:i+32], 2) for i in range(0, len(message), 32)]

    def __initialize_input(self, plaintext):
        # Format it to bytes
        binary_list = [format(byte, '08b') for byte in plaintext]
        # Add a binary 1 to the end
        binary_message = ''.join(binary_list) + '1'

        bit_len = (len(binary_message))  # Current bit length
        # Calculate and apply padding
        padding_required = self.__round_up_to_block(bit_len) - bit_len
        binary_message += '0' * padding_required
        binary_message += self.__return_plaintext_len(len(plaintext))

        return self.__partition_to_512_blocks(binary_message)