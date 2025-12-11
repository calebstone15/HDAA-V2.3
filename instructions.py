import tkinter as tk
from tkinter import Toplevel, Text

def run(app):
    # Create a new window
    instructions_window = Toplevel(app)
    instructions_window.title("Instructions")
    instructions_window.geometry("1200x800")  # Set the window size

    # Add a large text area for writing instructions
    text_area = Text(instructions_window, wrap='word', font=("Arial", 20))
    text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    # Insert a dummy paragraph
    text_area.tag_configure("center", justify='center')  # Configure a tag for centered text
    text_area.insert("1.0", "Welcome to the Hotfire Data Analysis App! Follow the instructions to learn how to use the app.    \n", "center")  # Add padding with spaces
    text_area.tag_configure("title", font=("Arial", 30, "bold"))  # Configure a tag for larger font
    text_area.tag_add("title", "1.0", "1.end")  # Apply the title tag to the first line
    text_area.insert("2.0", "\n")  # Add a blank line
    text_area.insert("3.0", "\n")  # Add a blank line
    text_area.insert("4.0", "\n")  # Add a blank line
    text_area.insert("5.0", "1. Load your CSV file containing the test data.\n")
    text_area.insert("6.0", "\n")  # Add a blank line
    text_area.insert("7.0", "2. Select the correct columns for each type of data and click confirm.\n")
    text_area.insert("8.0", "\n")  # Add a blank line
    text_area.insert("9.0", "3. Use the sliders to adjust the data downsampling and the amount of data to be added before and after the hotfire.\n")
    text_area.insert("10.0", "\n")  # Add a blank line
    text_area.insert("11.0", "4. Click on any of the quick plot functions and enter extra data (if required).\n")
    text_area.insert("12.0", "\n")  # Add a blank line
    text_area.insert("13.0", "5. Use the smoothing slider to smooth the data until appropriate.\n")
    text_area.insert("14.0", "\n")  # Add a blank line
    text_area.insert("15.0", "6. Click on the save button to save the data to a PNG file.\n")
    text_area.insert("16.0", "\n")  # Add a blank line
    text_area.insert("17.0", "7. If you would like to have a plot with more than one type of data, click on the custom plot button.\n")
    text_area.insert("18.0", "\n")  # Add a blank line
    text_area.insert("19.0", "8. You can then plot as many types of data as you want and save the same way as quick plots.\n")
    text_area.insert("20.0", "\n")  # Add a blank line
    text_area.insert("21.0", "9. The generate all plots button will generate all of the quick plots at once. Just make sure to input all required data.\n")
    text_area.insert("22.0", "\n")  # Add a blank line