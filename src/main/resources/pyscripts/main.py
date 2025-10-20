from taintAnalyzer import TaintAnalysis
from resultManager import AnalysisResultManager
from reportGenerator import MakeMD
from datetime import datetime

try:
    from claude_simple import send_to_claude
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

def create_result(output_folder, flows):
    path = output_folder + "/taint_result.txt"
    with open(path, 'w', encoding='utf-8') as file:  # 결과 파일 생성
        for (class_method, var), value in flows.items():
            file.write("Tainted Variable:\n")
            file.write(f"{var}\n")
            file.write("흐름 파악\n")
            for f in value:
                if isinstance(f[0], list):
                    for sub_f in f:
                        file.write(f"{sub_f}\n")
                else:
                    file.write(f"{f}\n")
            file.write("\n")


def print_result(flows):
    print("\nTainted flows:")
    for f in flows:
        print(f)
    print()


def __analyze_method(output_folder, tainted):
    json_file_path = output_folder + "/analysis_result.json"
    result = AnalysisResultManager(json_file_path)

    flows = tainted._priority_flow()

    for flow in flows:
        sensitivity = flow[0]  # 민감도 값

        for count in range(1, len(flow)):
            method_full_path = flow[count]
            big_parts = method_full_path.split(',')
            if len(big_parts) == 1:
                big_parts.append("")
            parts = big_parts[0].split('.')
            little_method_name = parts[1]

            cut_tree = tainted._get_cut_tree(little_method_name)
            current_path = tainted._file_path
            tree_position = tainted._get_position
            source_code = tainted._extract_method_source_code()
            method_name = method_full_path

            result.append(sensitivity, current_path, method_name, tree_position, cut_tree, source_code)

    result.save_to_json()  # 결과를 JSON 파일로 저장
    return json_file_path  # JSON 파일 경로 반환


def __run_claude_analysis(priority_flow, output_folder, api_key=None):
    """Claude 분석 실행"""
    if not CLAUDE_AVAILABLE:
        return

    try:
        result = send_to_claude(priority_flow, api_key)
        if result:
            # 결과 저장
            output_file = output_folder + "/llm_analysis_result.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"Claude 분석 결과 저장: {output_file}")
    except Exception as e:
        print(f"Claude 분석 오류: {e}")


def main(output_folder, api_key=None) :
    tainted = TaintAnalysis(output_folder)
    priority_flow = tainted._priority_flow()

    if not priority_flow:  # priority_flow가 비어있는 경우
        print("발견된 taint가 없습니다.")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 현재 시각을 'YYYY-MM-DD HH:MM:SS' 형식으로 저장

        with open(output_folder + "/analysis_result.md", "w") as md_file:
            md_file.write("# Taint Analysis Result\n")
            md_file.write("## Summary\n")
            md_file.write("No taint flows were detected during the analysis.\n\n")
            md_file.write("## Details\n")
            md_file.write("- **Analysis Time**: {}\n".format(current_time))  # 실제 시간 출력
            md_file.write("- **Output Folder**: {}\n\n".format(output_folder))
            md_file.write("The taint analysis did not identify any potential issues or vulnerabilities in the given codebase.\n")
            md_file.write("If you believe there should be taint flows detected, please review the input code or adjust the analysis parameters.\n")
            md_file.write("\n---\n")
    else:
        print_result(priority_flow)
        create_result(output_folder, tainted.flows)
        json_file_path = __analyze_method(output_folder, tainted)

        # Claude 분석 실행
        __run_claude_analysis(priority_flow, output_folder, api_key)

        make_md = MakeMD(output_folder + "/taint_result.txt", output_folder + "/analysis_result.md", priority_flow)
        make_md.make_md_file()


if __name__ == '__main__':
    import sys

    output_folder = sys.argv[1]
    api_key = sys.argv[2]
    print("api :", api_key)
    main(output_folder, api_key)