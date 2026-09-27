import javalang
import os
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed


def _parse_one(file_path):
    """Worker: read + parse a single Java file. Returns (file_path, source_code, tree, error)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        tree = javalang.parse.parse(source_code)
        return file_path, source_code, tree, None
    except (javalang.parser.JavaSyntaxError, javalang.parser.JavaParserError, SyntaxError) as e:
        return file_path, None, None, str(e)
    except Exception as e:
        return file_path, None, None, f"unexpected: {e}"


class ASTParser:
    """Java 파일 AST 파싱을 담당하는 클래스"""

    def __init__(self, max_workers=None):
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers or max(1, (os.cpu_count() or 2) - 1)

    def parse_java_files(self, folder_path):
        """주어진 폴더의 모든 Java 파일을 병렬 파싱하여 (file_path, tree) 리스트와 source_codes 딕셔너리를 반환"""
        java_files = [
            os.path.join(root, name)
            for root, _, files in os.walk(folder_path)
            for name in files
            if name.endswith('.java')
        ]

        trees = []
        source_codes = {}
        error_files = []

        if not java_files:
            self.logger.info("총 0개의 파일")
            return trees, source_codes

        # 작은 작업 묶음에서는 프로세스 오버헤드가 더 크므로 단일 스레드로 처리
        if len(java_files) <= 4:
            for fp in java_files:
                fp, src, tree, err = _parse_one(fp)
                self._collect(fp, src, tree, err, trees, source_codes, error_files)
        else:
            workers = min(self.max_workers, len(java_files))
            with ProcessPoolExecutor(max_workers=workers) as ex:
                for fut in as_completed(ex.submit(_parse_one, fp) for fp in java_files):
                    fp, src, tree, err = fut.result()
                    self._collect(fp, src, tree, err, trees, source_codes, error_files)

        total = len(java_files)
        self.logger.info(f"총 {total}개의 파일 중 {len(trees)}개 파싱 성공, {len(error_files)}개 파싱 실패")
        if error_files:
            self.logger.error("파싱 오류가 발생한 파일들:")
            for fp, err in error_files:
                self.logger.error(f"  - {fp}: {err}")

        return trees, source_codes

    def _collect(self, file_path, source_code, tree, error, trees, source_codes, error_files):
        if error is None:
            trees.append((file_path, tree))
            source_codes[file_path] = source_code
            self.logger.info(f"파싱 성공: {file_path}")
        else:
            error_files.append((file_path, error))
            self.logger.error(f"파싱 실패: {file_path}: {error}")
