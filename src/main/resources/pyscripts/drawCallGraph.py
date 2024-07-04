import javalang
import os
import sys

def parse_java_file(file_path):
    """ Parse a Java file and return its AST. """
    with open(file_path, 'r') as file:
        source_code = file.read()
    # Parse the source code to create an Abstract Syntax Tree (AST)
    tree = javalang.parse.parse(source_code)
    return tree

def get_method_calls(tree, class_name):
    """ Extract method calls from the AST.

    Args:
        tree: The AST of the Java file.
        class_name: The name of the class in the Java file.

    Returns:
        A list of tuples representing method calls.
    """
    method_calls = []

    # Traverse the AST to find all method declarations
    for _, node in tree.filter(javalang.tree.MethodDeclaration):
        current_method = f"{class_name} {node.name}"
        # Traverse the subtree of each method declaration to find method invocations
        for path, child in node:
            if isinstance(child, javalang.tree.MethodInvocation):
                # Determine the target class of the method call
                target_class = child.qualifier if child.qualifier else class_name
                method_name = child.member
                call_type = "M"  # Default call type is invokevirtual

                # Static method calls have a qualifier
                if child.qualifier:
                    call_type = "S"

                method_calls.append((call_type, current_method, target_class, method_name))

    return method_calls

def write_method_calls(output_file, method_calls):
    """ Write method calls to the output file with the specified format.

    Args:
        output_file: The path to the output file.
        method_calls: A list of tuples representing method calls.
    """
    with open(output_file, 'w') as f:
        for call_type, current_method, target_class, method_name in method_calls:
            f.write(f"{call_type}:{current_method} {target_class}.{method_name}\n")

def main(java_files_path, output_folder):
    """ Main function to process Java files and extract method calls.

    Args:
        java_files_path: The path to the Java files directory.
        output_folder: The folder where the output file will be saved.
    """
    output_file = os.path.join(output_folder, 'cfg_method_calls.txt')
    method_calls = []

    # Walk through the directory to find all Java files
    for root, _, files in os.walk(java_files_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                tree = parse_java_file(file_path)
                class_name = os.path.splitext(file)[0]  # Extract class name from file name
                method_calls.extend(get_method_calls(tree, class_name))

    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)
    # Write the method calls to the output file
    write_method_calls(output_file, method_calls)
    print(f"Method calls written successfully to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <java_files_path> <output_folder>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
