import tempfile

# Create a temporary file
with tempfile.TemporaryFile(mode='w+t', encoding='utf-8') as temp_file:
    # Write data to the temporary file
    temp_file.write("This is some temporary data.\n")
    temp_file.write("More temporary data.")

    # Seek to the beginning to read the data
    temp_file.seek(0)

    # Read data from the temporary file
    content = temp_file.read()
    print(content)

# The temporary file is automatically deleted when exiting the 'with' block