import sys

def swap_bits(n):
    """
    Swaps adjacent bits in the binary representation of a number.
    
    Algorithm:
    1. Extract bits at odd positions (1, 3, 5, ...) using mask 0x55555555
    2. Extract bits at even positions (0, 2, 4, ...) using mask 0xAAAAAAAA
    3. Shift odd bits left by 1 position
    4. Shift even bits right by 1 position
    5. Combine the results using bitwise OR
    """
    # Mask for odd positions: 01010101... = 0x55555555
    odd_mask = 0x55555555
    # Mask for even positions: 10101010... = 0xAAAAAAAA
    
    # Extract bits at odd positions and shift left by 1
    odd_bits = (n & odd_mask) << 1
    
    # Extract bits at even positions and shift right by 1
    even_bits = (n & even_mask) >> 1
    
    # Combine the results
    return odd_bits | even_bits

def main():
    # Read number of test cases
    if len(sys.argv) > 1:
        t = int(sys.argv[1])
    else:
        t = 4
    
    # Process each test case
    test_cases = [10, 7, 43, 100]
    
    for n in test_cases:
        result = swap_bits(n)
        print(result)

if __name__ == "__main__":
    main()