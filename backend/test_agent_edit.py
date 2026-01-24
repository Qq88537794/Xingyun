"""
Agent 编辑操作测试脚本（扩展版）
用于验证 AI 对文档的各类编辑操作是否生效，包括：
- 基础编辑：字符删除、替换
- 格式化：大小写转换、空格处理
- 内容清理：删除数字、URL等
- 复杂操作：添加行号、Markdown处理、批量替换

运行：
    cd backend
    .\venv\Scripts\Activate.ps1
    python test_agent_edit.py
"""

import requests
import json
import os
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
API_URL = f"{BASE_URL}/api"
ADMIN_TOKEN = os.getenv('ADMIN_DEV_TOKEN', 'dev-admin-token-2026-xingyun')

VERBOSE = True

results = []


def print_request(method, url, headers=None, data=None, files=None):
    if not VERBOSE:
        return
    print("📤 请求:")
    print(f"   {method} {url}")
    if headers:
        print(f"   Headers: {json.dumps(dict(headers), ensure_ascii=False, indent=2)}")
    if data:
        print(f"   Body: {json.dumps(data, ensure_ascii=False, indent=2)}")
    if files:
        print(f"   Files: {list(files.keys())}")
    print()


def print_response(resp):
    if not VERBOSE:
        return
    print("📥 响应:")
    print(f"   Status: {resp.status_code}")
    try:
        print(f"   Body: {json.dumps(resp.json(), ensure_ascii=False, indent=2)[:2000]}")
    except Exception:
        print(f"   Body: {resp.text[:2000]}")
    print()


def log_result(name, success, message, details=None):
    results.append({
        'test': name,
        'success': success,
        'message': message,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })
    status = 'PASS' if success else 'FAIL'
    print(f"{status} | {name} - {message}")
    if details:
        print(json.dumps(details, ensure_ascii=False, indent=2))
    print()


def get_headers():
    return {
        'Authorization': f'Bearer {ADMIN_TOKEN}',
        'Content-Type': 'application/json'
    }


def test_delete_character(project_id=None):
    """删除字符 'Z' 用例"""
    original = "这是一个用于测试的文本。包含特殊字符：Z Z Z，需要删除所有大写字母Z。"
    
    payload = {
        'message': "请删除文本中的所有大写字母 'Z'",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('delete_char', False, f'HTTP {resp.status_code}', resp.json() if resp.headers.get('Content-Type','').startswith('application/json') else {'text': resp.text})
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = ('Z' not in modified)
        log_result('delete_char', success, '删除字符 Z', {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('delete_char', False, f'异常: {str(e)}')


def test_replace_character(project_id=None):
    """替换字符 X -> Q 用例"""
    original = "样例文本: X出现在这里: X X X，请将所有的 X 替换为 Q。"
    
    payload = {
        'message': "请将文本中的所有大写字母 'X' 替换为 'Q'",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('replace_char', False, f'HTTP {resp.status_code}', resp.json() if resp.headers.get('Content-Type','').startswith('application/json') else {'text': resp.text})
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = ('X' not in modified and 'Q' in modified)
        log_result('replace_char', success, "替换 X -> Q", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('replace_char', False, f'异常: {str(e)}')


def test_uppercase_conversion(project_id=None):
    """转大写用例"""
    original = "hello world, this is a test."
    
    payload = {
        'message': "请将文本全部转换为大写字母",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('uppercase', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = (modified == original.upper())
        log_result('uppercase', success, "转大写", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('uppercase', False, f'异常: {str(e)}')


def test_remove_numbers(project_id=None):
    """删除数字用例"""
    original = "订单号: 12345, 价格: 99元, 电话: 138-0000-0000"
    
    payload = {
        'message': "请删除文本中的所有数字",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('remove_numbers', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = not any(c.isdigit() for c in modified)
        log_result('remove_numbers', success, "删除数字", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('remove_numbers', False, f'异常: {str(e)}')


def test_remove_extra_spaces(project_id=None):
    """删除多余空格用例"""
    original = "这是   一个    有很多    空格的     文本。"
    
    payload = {
        'message': "请将文本中的多个连续空格替换为单个空格",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('remove_spaces', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        # 检查是否没有连续两个空格
        success = '  ' not in modified
        log_result('remove_spaces', success, "删除多余空格", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('remove_spaces', False, f'异常: {str(e)}')


def test_add_line_numbers(project_id=None):
    """添加行号用例"""
    original = "第一行内容\n第二行内容\n第三行内容"
    
    payload = {
        'message': "请在每行前面添加行号，格式为 '1. ', '2. ' 等",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('add_line_numbers', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        # 检查是否包含行号
        success = '1. ' in modified and '2. ' in modified and '3. ' in modified
        log_result('add_line_numbers', success, "添加行号", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('add_line_numbers', False, f'异常: {str(e)}')


def test_markdown_to_plain(project_id=None):
    """Markdown转纯文本用例"""
    original = "# 标题\n\n这是**粗体**和*斜体*文本。\n\n- 列表项1\n- 列表项2"
    
    payload = {
        'message': "请移除文本中的所有Markdown格式标记（#、*、-等），保留纯文本内容",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('markdown_clean', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        # 检查是否没有Markdown标记
        success = '#' not in modified and '**' not in modified and '- ' not in modified[:10]
        log_result('markdown_clean', success, "清理Markdown", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('markdown_clean', False, f'异常: {str(e)}')


def test_batch_replace(project_id=None):
    """批量替换用例"""
    original = "苹果很好吃，香蕉也不错，橙子也很棒。"
    
    payload = {
        'message': "请将文本中的'苹果'替换为'Apple'，'香蕉'替换为'Banana'，'橙子'替换为'Orange'",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('batch_replace', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = 'Apple' in modified and 'Banana' in modified and 'Orange' in modified
        log_result('batch_replace', success, "批量替换", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('batch_replace', False, f'异常: {str(e)}')


def test_remove_urls(project_id=None):
    """删除URL用例"""
    original = "访问我们的网站 https://example.com 或 http://test.org 了解更多信息。"
    
    payload = {
        'message': "请删除文本中的所有URL链接",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('remove_urls', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = 'http' not in modified.lower()
        log_result('remove_urls', success, "删除URL", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('remove_urls', False, f'异常: {str(e)}')


def test_remove_emails(project_id=None):
    """删除邮箱用例"""
    original = "请联系 a@test.com 或 b@example.org 获取更多信息。"
    
    payload = {
        'message': "请删除文本中的所有邮箱地址",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('remove_emails', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = '@' not in modified
        log_result('remove_emails', success, "删除邮箱", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('remove_emails', False, f'异常: {str(e)}')


def test_remove_blank_lines(project_id=None):
    """删除空行用例"""
    original = "第一行\n\n\n第二行\n\n第三行"
    
    payload = {
        'message': "请删除文本中的所有空行",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('remove_blank_lines', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        lines = modified.splitlines()
        success = all(line.strip() != '' for line in lines)
        log_result('remove_blank_lines', success, "删除空行", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('remove_blank_lines', False, f'异常: {str(e)}')


def test_trim_lines(project_id=None):
    """去除行首尾空格用例"""
    original = "  第一行  \n 第二行\n第三行   "
    
    payload = {
        'message': "请去除每一行的首尾空格",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('trim_lines', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        lines = modified.splitlines()
        success = all(line == line.strip() for line in lines)
        log_result('trim_lines', success, "去除首尾空格", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('trim_lines', False, f'异常: {str(e)}')


def test_dedupe_lines(project_id=None):
    """行去重用例"""
    original = "苹果\n香蕉\n苹果\n橙子\n香蕉"
    
    payload = {
        'message': "请对文本按行去重，保留首次出现的顺序",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('dedupe_lines', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        lines = [l for l in modified.splitlines() if l.strip()]
        success = len(lines) == len(set(lines))
        log_result('dedupe_lines', success, "行去重", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('dedupe_lines', False, f'异常: {str(e)}')


def test_replace_tabs_with_spaces(project_id=None):
    """Tab替换为空格用例"""
    original = "第一列\t第二列\t第三列"
    
    payload = {
        'message': "请将所有制表符替换为单个空格",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('replace_tabs', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = '\t' not in modified
        log_result('replace_tabs', success, "替换Tab", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('replace_tabs', False, f'异常: {str(e)}')


def test_merge_lines(project_id=None):
    """合并多行用例"""
    original = "第一行内容\n第二行内容\n第三行内容"
    
    payload = {
        'message': "请将所有换行替换为单个空格，形成一行文本",
        'project_id': project_id,
        'mode': 'simple',
        'document_content': original
    }

    url = f"{API_URL}/ai/chat"
    headers = get_headers()
    print_request('POST', url, headers=headers, data=payload)

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        print_response(resp)

        if resp.status_code != 200:
            log_result('merge_lines', False, f'HTTP {resp.status_code}')
            return

        data = resp.json().get('data', {})
        operations = data.get('operations', [])
        if operations and operations[0].get('content'):
            modified = operations[0]['content']
        else:
            modified = data.get('message', '')
        
        success = '\n' not in modified
        log_result('merge_lines', success, "合并多行", {'original': original, 'modified': modified[:1000]})

    except Exception as e:
        log_result('merge_lines', False, f'异常: {str(e)}')


def generate_report():
    report_file = f"AGENT_EDIT_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({'summary': {'total': len(results), 'passed': sum(1 for r in results if r['success']), 'failed': sum(1 for r in results if not r['success'])}, 'results': results}, f, ensure_ascii=False, indent=2)
    print(f"报告已保存到: {report_file}")


if __name__ == '__main__':
    print('\n=== Agent 编辑操作测试（扩展版）===')
    print('测试场景包括：字符操作、格式化、内容清理、结构整理、批量处理\n')

    # 基础编辑操作
    print('--- 基础编辑操作 ---')
    test_delete_character()
    test_replace_character()
    
    # 格式化操作
    print('\n--- 格式化操作 ---')
    test_uppercase_conversion()
    test_remove_extra_spaces()
    test_replace_tabs_with_spaces()
    test_merge_lines()
    
    # 内容清理操作
    print('\n--- 内容清理操作 ---')
    test_remove_numbers()
    test_remove_urls()
    test_remove_emails()
    test_remove_blank_lines()
    test_trim_lines()
    test_dedupe_lines()
    
    # 复杂操作
    print('\n--- 复杂操作 ---')
    test_add_line_numbers()
    test_markdown_to_plain()
    test_batch_replace()

    generate_report()
    
    # 输出统计
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    print(f'\n测试完成！')
    print(f'总计: {total} | 通过: {passed} | 失败: {failed}')
    print(f'通过率: {passed/total*100:.1f}%' if total > 0 else '通过率: N/A')
