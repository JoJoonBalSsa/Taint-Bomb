import os
import hashlib


def calculate_sha256(file_path):
    """주어진 파일의 SHA-256 해시값을 계산합니다."""
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as file:
        for byte_block in iter(lambda: file.read(4096), b''):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def python_in_directory(directory_path, exclude_file='create_hash.py', output_file='check_hash'):
    """디렉토리 내의 .py 파일들의 SHA-256 해시값을 계산하고 결과를 output_file에 저장합니다."""
    file_hashes = {}

    # 모든 .py 파일을 탐색하여 해시값 계산
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py') and file != exclude_file:
                file_path = os.path.join(root, file)
                file_hash = calculate_sha256(file_path)
                file_name = file.replace('.py', '')
                file_hashes[file_name] = file_hash

    # 딕셔너리를 파일에 저장
    with open(os.path.join(directory_path, output_file), 'w') as output:
        for file_name, file_hash in sorted(file_hashes.items()):
            output.write(f"{file_name} {file_hash}\n")
    print(f"SHA-256 해시값이 {output_file} 파일에 저장되었습니다.")


# 사용 예시
python_path = './'
python_in_directory(python_path)