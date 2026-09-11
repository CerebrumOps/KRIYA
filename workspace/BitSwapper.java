import java.util.Scanner;

public class BitSwapper {
    
    /**
     * Swaps adjacent bits in the binary representation of a number.
     * 
     * Algorithm:
     * 1. Extract bits at odd positions (1, 3, 5, ...) using mask 0x55555555
     * 2. Extract bits at even positions (0, 2, 4, ...) using mask 0xAAAAAAAA
     * 3. Shift odd bits left by 1 position
     * 4. Shift even bits right by 1 position
     * 5. Combine the results using bitwise OR
     */
    public static int swapBits(int n) {
        // Mask for odd positions: 01010101... = 0x55555555
        int oddMask = 0x55555555;
        // Mask for even positions: 10101010... = 0xAAAAAAAA
        
        // Extract bits at odd positions and shift left by 1
        int oddBits = (n & oddMask) << 1;
        
        // Extract bits at even positions and shift right by 1
        int evenBits = (n & evenMask) >> 1;
        
        // Combine the results
        return oddBits | evenBits;
    }
    
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        
        // Read number of test cases
        if (scanner.hasNextInt()) {
            int t = scanner.nextInt();
            
            // Process each test case
            for (int i = 0; i < t; i++) {
                if (scanner.hasNextInt()) {
                    int n = scanner.nextInt();
                    int result = swapBits(n);
                    System.out.println(result);
                }
            }
        }
        
        scanner.close();
    }
}