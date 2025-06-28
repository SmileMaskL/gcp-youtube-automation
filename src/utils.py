# src/utils.py
import os
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def cleanup_local_files(file_paths: list[str]):
    """
    지정된 파일 경로들을 삭제합니다.
    """
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logging.info(f"Cleaned up local file: {file_path}")
            except OSError as e:
                logging.error(f"Error removing file {file_path}: {e}", exc_info=True)
        else:
            logging.warning(f"File not found for cleanup: {file_path}")

def cleanup_directory(directory_path: str):
    """
    지정된 디렉토리와 그 안의 모든 내용을 삭제합니다.
    """
    if os.path.exists(directory_path) and os.path.isdir(directory_path):
        try:
            shutil.rmtree(directory_path)
            logging.info(f"Cleaned up directory: {directory_path}")
        except OSError as e:
            logging.error(f"Error removing directory {directory_path}: {e}", exc_info=True)
    else:
        logging.warning(f"Directory not found for cleanup: {directory_path}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # 테스트 파일 및 디렉토리 생성
    test_file1 = "test_file_to_delete1.txt"
    test_file2 = "test_file_to_delete2.txt"
    test_dir = "test_dir_to_delete"
    test_file_in_dir = os.path.join(test_dir, "file_in_dir.txt")

    os.makedirs(test_dir, exist_ok=True)
    with open(test_file1, "w") as f: f.write("test")
    with open(test_file2, "w") as f: f.write("test")
    with open(test_file_in_dir, "w") as f: f.write("test")

    print("Created test files and directory.")

    # 파일 정리 테스트
    cleanup_local_files([test_file1, test_file2, "non_existent_file.txt"])

    # 디렉토리 정리 테스트
    cleanup_directory(test_dir)

    print("Cleanup tests completed.")
