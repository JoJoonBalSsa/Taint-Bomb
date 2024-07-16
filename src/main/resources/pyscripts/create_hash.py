import os
import hashlib

def calculate_md5(file_path):
    """주어진 파일의 MD5 해시값을 계산합니다."""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as file:
        for byte_block in iter(lambda: file.read(4096), b''):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

def hash_files_in_directory(directory_path, exclude_file='create_hash.py', output_file='check_hash'):
    """디렉토리 내의 .py 파일들의 MD5 해시값을 계산하고 결과를 output_file에 저장합니다."""
    with open(directory_path + output_file, 'w') as output:
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py') and file != exclude_file:
                    file_path = os.path.join(root, file)
                    file_hash = calculate_md5(file_path)
                    file_name = file.replace('.py', '')
                    output.write(f"{file_name} {file_hash}\n")
    print(f"MD5 해시값이 {output_file} 파일에 저장되었습니다.")

# 사용 예시
directory_path = 'src/main/resources/pyscripts/'
hash_files_in_directory(directory_path)
