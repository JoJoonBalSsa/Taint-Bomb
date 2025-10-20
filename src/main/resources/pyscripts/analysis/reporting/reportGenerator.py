import re
import os
import datetime
from collections import defaultdict, Counter

class MakeMD:
    def __init__(self, input_file='taint_result.txt', output_file='analysis_result.md', sensitivity_flow=[]):
        self.input_file = input_file
        self.output_file = output_file
        self.sensitivity_flow = sensitivity_flow

    def parse_result_file(self):
        tainted_variables = []
        if not os.path.exists(self.input_file):
            print(f"Error: Input file '{self.input_file}' not found.")
            return tainted_variables

        with open(self.input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        i = 0
        f = 0
        while i < len(lines):
            line = lines[i].strip()
            if line is None == "":
                raise ValueError("No Line Error")
            if line.startswith("Tainted Variable:"):
                variable_name = lines[i + 1].strip()
                flow = []
                i += 3  # 'Tainted Variable:' 줄과 변수 이름 줄을 건너뜁니다
                while i < len(lines) and lines[i].strip().startswith('['):
                    try:
                        clean_line = self.clean_flow(lines[i].strip())
                        for flow_node in clean_line:
                            flow.append(flow_node)
                    except ValueError:
                        print(f"Warning: Unable to parse line: {lines[i].strip()}")
                    i += 1
                tainted_variables.append({"variable": variable_name, "flow": flow, "sensitivity" : self.sensitivity_flow[f][0]})
                f += 1
                continue
            i += 1

        sorted_results = sorted(tainted_variables, key=lambda x: x["sensitivity"], reverse=True)

        return sorted_results

    def clean_flow(self, flow_string):
        # 대괄호 제거
        cleaned_string = flow_string.strip()[1:-1]

        # 정규 표현식을 사용하여 원하는 항목 추출
        items = re.findall(r"'([^']+)'", cleaned_string)

        # 각 항목에서 쉼표 제거 및 앞뒤 공백 제거
        cleaned_items = [item.replace(',', '').strip() for item in items]

        return cleaned_items

    def create_call_graph_svg(self, flow):
        nodes = flow
        edges = list(zip(flow[:-1], flow[1:]))
        node_counts = Counter(nodes)

        class_nodes = defaultdict(list)
        for node in dict.fromkeys(nodes):  # 중복 제거하면서 순서 유지
            class_name, method = node.rsplit('.', 1)
            class_nodes[class_name].append(method)

        svg_width = 1200  # 너비 증가
        svg_height = max(len(max(class_nodes.values(), key=len)) * 60, 400)
        class_width = svg_width / len(class_nodes)
        node_radius = 5
        font_size = 12

        svg = [f'''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
            <style>
                .node {{ fill: blue; }}
                .node-text {{ font-size: {font_size}px; }}
                .class-label {{ fill: white; }}
                .class-text {{ font-size: 14px; font-weight: bold; }}
                .edge {{ stroke: black; fill: none; stroke-width: 1.5; }}
                .background {{ fill: white; }}
                .duplicate-count {{ font-size: 10px; fill: red; font-weight: bold; }}
            </style>
            <rect width="100%" height="100%" class="background"/>
        ''']

        node_positions = {}

        for i, (class_name, methods) in enumerate(class_nodes.items()):
            class_x = i * class_width + class_width / 2
            label_width = len(class_name) * 10 + 20
            label_height = 30

            svg.append(f'<rect x="{class_x - label_width/2}" y="10" width="{label_width}" height="{label_height}" rx="5" ry="5" fill="#4a4a4a"/>')
            svg.append(f'<text x="{class_x}" y="30" class="class-text" text-anchor="middle" fill="white">{class_name}</text>')

            for j, method in enumerate(methods):
                full_node_name = f"{class_name}.{method}"
                x = class_x
                y = 60 + j * 50
                node_positions[full_node_name] = (x, y)
                svg_id = re.sub(r'[^\w]', '_', full_node_name)
                count = node_counts[full_node_name]

                svg.append(f'<g id="{svg_id}">')
                svg.append(f'<circle cx="{x}" cy="{y}" r="{node_radius}" class="node" />')
                svg.append(f'<text x="{x + node_radius + 5}" y="{y + 5}" class="node-text">{method}</text>')
                if count > 1:
                    svg.append(f'<text x="{x + node_radius + 5 + len(method) * 7}" y="{y + 5}" class="duplicate-count"> ({count})</text>')
                svg.append('</g>')

        # 엣지 그리기 (중복 제거)
        drawn_edges = set()
        for start, end in edges:
            edge = (start, end)
            if edge in drawn_edges or start == end:
                continue

            if start in node_positions and end in node_positions:
                x1, y1 = node_positions[start]
                x2, y2 = node_positions[end]

                dx = x2 - x1
                dy = y2 - y1
                dist = (dx**2 + dy**2)**0.5

                cx1 = x1 + dx * 0.25
                cy1 = y1 + dy * 0.1
                cx2 = x2 - dx * 0.25
                cy2 = y2 - dy * 0.1

                curve_height = min(100, max(20, dist * 0.2))

                if y2 > y1:
                    cy1 -= curve_height
                    cy2 -= curve_height
                else:
                    cy1 += curve_height
                    cy2 += curve_height

                svg.append(f'<path d="M{x1},{y1} C{cx1},{cy1} {cx2},{cy2} {x2},{y2}" class="edge" marker-end="url(#arrowhead)" />')
                drawn_edges.add(edge)

        svg.append('''
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="black" />
                </marker>
            </defs>
        ''')

        svg.append('</svg>')
        return ''.join(svg)

    def make_md_file(self):
        tainted_variables = self.parse_result_file()
        print(tainted_variables)
        if not tainted_variables:
            print("Error: No tainted variables found. The markdown file will not be created.")
            return

        def create_anchor(text):
            # 소문자로 변환하고 특수 문자 제거
            anchor = re.sub(r'[^\w\- ]', '', text.lower())
            # 공백을 대시로 변환
            anchor = anchor.replace(' ', '-')
            return anchor

        with open(self.output_file, 'w', encoding='utf-8') as md_file:
            # 파일 헤더 및 목차 작성
            md_file.write(f"# 결과 보고서\n\n")
            md_file.write(f"**생성일:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            md_file.write(f"**생성 도구:** Taint Bomb\n\n")

            # 목차 작성
            md_file.write("## 목차\n")
            md_file.write("- [개요](#개요)\n")
            for i, var_info in enumerate(tainted_variables, 1):
                anchor = create_anchor(f"흐름 {i} {var_info['variable']}")
                if var_info['sensitivity'] == 3:
                    md_file.write(f"- [흐름 {i}: {var_info['variable']}](#{anchor})" + " - 상\n")
                elif var_info['sensitivity'] == 2:
                    md_file.write(f"- [흐름 {i}: {var_info['variable']}](#{anchor})" + " - 중\n")
                else:
                    md_file.write(f"- [흐름 {i}: {var_info['variable']}](#{anchor})" + " - 하\n")
            md_file.write("\n")

            # 개요 작성
            md_file.write("## 개요\n")
            md_file.write("이 보고서는 코드베이스에 대한 분석 결과를 제공하며, 잠재적인 보안 위험과 취약점을 식별합니다.\n")
            md_file.write("각 섹션에는 오염된 데이터의 흐름을 시각화한 콜 그래프와 상세 정보가 포함되어 있습니다.\n\n")

            # Write call graph section
            md_file.write("## 콜 그래프\n")
            md_file.write("아래는 애플리케이션에서 오염된 데이터의 흐름을 나타내는 콜 그래프입니다. 각 그래프 뒤에는 관련된 오염된 변수에 대한 상세 분석이 이어집니다.\n\n")

            # 각 흐름에 대한 콜 그래프와 상세 정보 작성
            for i, var_info in enumerate(tainted_variables, 1):
                if var_info['sensitivity'] == 3:
                    md_file.write(f"## 흐름 {i}: `{var_info['variable']}`\n\n")
                elif var_info['sensitivity'] == 2:
                    md_file.write(f"## 흐름 {i}: `{var_info['variable']}`\n\n")
                else:
                    md_file.write(f"## 흐름 {i}: `{var_info['variable']}`\n\n")

                # SVG 콜 그래프 생성 및 삽입
                svg_content = self.create_call_graph_svg(var_info['flow'])
                md_file.write("<div class='call-graph'>\n")
                md_file.write(svg_content)
                md_file.write("</div>\n\n")

                # 흐름 상세 정보 작성
                if var_info['sensitivity'] == 3:
                    md_file.write(f"**민감도:** `상`\n\n")
                elif var_info['sensitivity'] == 2:
                    md_file.write(f"**민감도:** `중`\n\n")
                else:
                    md_file.write(f"**민감도:** `하`\n\n")
                md_file.write(f"**오염된 변수:** `{var_info['variable']}`\n\n")
                md_file.write("**데이터 흐름:**\n")
                md_file.write("```\n")
                md_file.write(" -> ".join(var_info['flow']))
                md_file.write("\n```\n\n")

            # CSS 스타일 추가
            md_file.write("<style>\n")
            md_file.write(".call-graph { overflow: auto; max-width: 100%; max-height: 600px; border: 1px solid #ddd; margin-bottom: 20px; }\n")
            md_file.write(".call-graph svg { min-width: 100%; min-height: 100%; }\n")
            md_file.write("</style>\n")

        print(f"\nMarkdown 보고서가 생성되었습니다: {self.output_file}")