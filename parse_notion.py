#!/usr/bin/env python3
import json
import sys

def parse_block(block):
    block_type = block.get('type')
    result = ""
    
    if block_type == 'paragraph':
        rich_text = block.get('paragraph', {}).get('rich_text', [])
        text = ''.join([t.get('plain_text', '') for t in rich_text])
        if text:
            result += f"{text}\n"
    
    elif block_type in ['heading_1', 'heading_2', 'heading_3', 'heading_4']:
        level = block_type.split('_')[1]
        heading = block.get(block_type, {}).get('rich_text', [])
        text = ''.join([t.get('plain_text', '') for t in heading])
        if text:
            prefix = '#' * int(level)
            result += f"\n{prefix} {text}\n"
    
    elif block_type == 'bulleted_list_item':
        rich_text = block.get('bulleted_list_item', {}).get('rich_text', [])
        text = ''.join([t.get('plain_text', '') for t in rich_text])
        if text:
            result += f"  - {text}\n"
    
    elif block_type == 'numbered_list_item':
        rich_text = block.get('numbered_list_item', {}).get('rich_text', [])
        text = ''.join([t.get('plain_text', '') for t in rich_text])
        if text:
            result += f"  {text}\n"
    
    return result

def main():
    if len(sys.argv) != 2:
        print("Usage: python parse_notion.py <json_file>")
        return
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    blocks = data.get('results', [])
    output = []
    
    for block in blocks:
        output.append(parse_block(block))
    
    print(''.join(output))

if __name__ == '__main__':
    main()
