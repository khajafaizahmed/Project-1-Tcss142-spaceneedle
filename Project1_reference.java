/*
 * Course: TCSS142 - Programming Principles
 * File Name: Project1.java
 * Assignment: Project 1
 * Due Date: Oct/24/2025
 * Instructor: Dr. Liu
 */

public class Project1_reference{

/**
 * This program draws an ASCI image of the Space Needle.
 * The {@value #SIZE} sets the scale of the output image.
 *
 * @author Faiz Ahmed
 * @version 10/14/2025
 *
 */

    /**
     * The user defined scale factor for controling the size of the figure.
     * <p>
     *
     */
    public static final int SIZE = 2;


    /**
     * This is the entry point of the program
     *
     */
    public static final void main (String[] args){

        //The complex figure is composed of multiple parts, each of which is drawn by the following methods

        drawNeedle();  // draw the spire

        drawTopSaucer();

        drawWindows(); // draws the windows

        drawBottomSaucer();

        drawNeedle(); // draw the support structure

        drawPipe();

        drawTopSaucer();

        drawWindows(); // dreaw the foundation

    }

    /**
     * Outputs the spire of the Space Needle.
     * Can also be used for the support structure.
     */
    public static void drawNeedle(){

        // counting the number of lines
        for (int i = 1; i <= SIZE; i++){

            // counting and printing the number of empty spaces
            for(int j = 1; j<= 3 * SIZE; j++){

                System.out.print(" ");
            }
            System.out.print("/\\");
            System.out.println();
        }
    }


    /**
     * Outputs the top saucer of the Space Needle.
     * Can also be used for the base structure.
     */
    public static void drawTopSaucer(){

        //loop through the number of lines
        for (int i = 1; i <= SIZE; i++){

            //counts and prints the number of empty spaces to the right
            for(int j = 1; j<= (-3 * i + 3 * SIZE); j++){

                System.out.print(" ");
            }

            System.out.print("__/");

            //counts and prints the number of underscores to the right
            for(int k = 1; k <= (3 * i -3); k++){
                System.out.print("_");
            }

            System.out.print("/\\");

            //counts and prints the number of underscores to the left
            for(int k = 1; k <= (3 * i -3); k++){
                System.out.print("_");
            }

            System.out.print("\\__");

            System.out.println();
        }
    }



    /**
     * Outputs the windows section of the Space Needle.
     * Can also be used for the fundation of the figure.
     */

    public static void drawWindows(){

        System.out.print("{");

        // counts and prints the number of []
        for(int i = 1; i <= 3 * SIZE; i++){
            System.out.print("[]");
        }

        System.out.println("}");
    }


    /**
     * Outputs the botom saucer of the Space Needle.
     *
     */
    public static void drawBottomSaucer(){

        //loops through the number of lines
        for(int i = 1; i <= SIZE; i++){

            // counts and prints the number of empty spaces
            for(int j = 1; j <= (2 * i - 2); j++){

                System.out.print(" ");

            }

            System.out.print("\\_");

            // counts and prints the number of "()"

            for(int j = 1; j <= (-2 * i + 3 * SIZE + 1); j++){

                System.out.print("()");

            }

            System.out.print("_/");

            System.out.println();
        }
    }

    /**
     * Outputs the column of the Space Needle.
     *
     */

    public static void drawPipe(){

        // counts the number of blocks
        for (int i = 1; i <= SIZE; i ++){

            // counts the number of lines in each block
            for (int j = 1; j <= 4; j++){

                //Counts the number of empty spaces
                for (int m = 1; m <= (3 * SIZE - 3); m++) {

                    System.out.print(" ");
                }

                System.out.print("|\"\"\\/\"\"|");
                System.out.println();

            }
        }
    }




}