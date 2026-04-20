#!/bin/bash

show_usage() {
    echo "============================================"
    echo "       NanoBOT Gateway 启动器"
    echo "============================================"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -l, --list     列出所有实例及其状态"
    echo "  -a, --all      启动所有配置"
    echo "  -k, --kill     停止运行中的实例"
    echo "  <数字>         启动指定索引的实例"
    echo ""
    echo "示例:"
    echo "  $0              # 显示帮助"
    echo "  $0 -l           # 列出所有实例"
    echo "  $0 -a           # 启动所有实例"
    echo "  $0 -k           # 停止实例"
    echo "  $0 1            # 启动索引为 1 的实例"
    exit 0
}

if [ $# -eq 0 ]; then
    show_usage
fi

POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            ;;
        -l|--list)
            LIST_MODE=1
            shift
            ;;
        -a|--all)
            ALL_MODE=1
            shift
            ;;
        -k|--kill)
            KILL_MODE=1
            shift
            ;;
        *)
            if [[ "$1" =~ ^[0-9]+$ ]]; then
                POSITIONAL+=("$1")
            else
                echo "未知选项: $1"
                show_usage
            fi
            shift
            ;;
    esac
done

set -- "${POSITIONAL[@]}"

NANOBOTS_DIR="./.nanobots"
CONFIG_PATH_PREFIX="$NANOBOTS_DIR"
LOG_PATH_PREFIX="/app/logs"

declare -A CONFIG_MAP
declare -A CONFIG_PATH
declare -A LOG_PATH
OPTIONS=()

if [ -d "$NANOBOTS_DIR" ]; then
    for entry in "$NANOBOTS_DIR"/*; do
        if [ -d "$entry" ]; then
            folder_name=$(basename "$entry")
            if [[ "$folder_name" == .* ]]; then
                c_name="${folder_name:1}"
            else
                c_name="$folder_name"
            fi

            idx=${#OPTIONS[@]}
            idx=$((idx + 1))
            OPTIONS+=("$idx")

            CONFIG_MAP["$idx"]="$c_name"
            CONFIG_PATH["$c_name"]="$CONFIG_PATH_PREFIX/$folder_name/config.json"
            LOG_PATH["$c_name"]="$LOG_PATH_PREFIX/$c_name.log"
        fi
    done
fi

execute_command() {
    local choice="$1"
    
    case "$choice" in
        l|L)
            echo ""
            echo "============================================"
            echo "       可用实例列表"
            echo "============================================"
            echo ""
            for idx in "${OPTIONS[@]}"; do
                c_name="${CONFIG_MAP[$idx]}"
                config_file="${CONFIG_PATH[$c_name]}"
                log_file="${LOG_PATH[$c_name]}"
                status="X 配置文件不存在"
                if [ -f "$config_file" ]; then
                    pid=$(pgrep -f "gateway.*$config_file" 2>/dev/null | head -1)
                    if [ -n "$pid" ]; then
                        status="V 运行中 (PID: $pid)"
                    else
                        status="- 已停止"
                    fi
                fi
                echo "  [$idx] $c_name"
                echo "      配置: $config_file"
                echo "      日志: $log_file"
                echo "      状态: $status"
                echo ""
            done
            echo "============================================"
            exit 0
            ;;
        a|A)
            echo ""
            echo "正在启动所有配置..."
            for idx in "${OPTIONS[@]}"; do
                C_NAME="${CONFIG_MAP[$idx]}"
                CONFIG_FILE="${CONFIG_PATH[$C_NAME]}"
                LOG_FILE="${LOG_PATH[$C_NAME]}"

                if [ ! -f "$CONFIG_FILE" ]; then
                    echo "X 配置文件不存在: $CONFIG_FILE"
                    continue
                fi

                LOG_DIR=$(dirname "$LOG_FILE")
                mkdir -p "$LOG_DIR"

                echo "> 启动 $C_NAME..."
                C_NAME=$C_NAME nohup python -m nanobot gateway --config "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &
                echo "V $C_NAME 已启动 (PID: $!)"
            done
            echo ""
            echo "V 所有配置已启动"
            exit 0
            ;;
        k|K)
            echo ""
            echo "============================================"
            echo "       停止实例"
            echo "============================================"
            echo ""

            running_instances=()
            for idx in "${OPTIONS[@]}"; do
                c_name="${CONFIG_MAP[$idx]}"
                config_file="${CONFIG_PATH[$c_name]}"
                if [ -f "$config_file" ]; then
                    pids=$(pgrep -f "gateway.*$config_file" 2>/dev/null)
                    if [ -n "$pids" ]; then
                        running_instances+=("$idx|$c_name|$pids")
                    fi
                fi
            done

            if [ ${#running_instances[@]} -eq 0 ]; then
                echo "没有运行中的实例"
                echo ""
                exit 0
            fi

            echo "运行中的实例:"
            echo ""
            for info in "${running_instances[@]}"; do
                IFS='|' read -r idx c_name pids <<< "$info"
                echo "  [$idx] $c_name (PID: $pids)"
            done
            echo "  [a] 停止所有"
            echo "  [q] 返回"
            echo ""
            read -p "请输入选项: " kill_choice

            case "$kill_choice" in
                a|A)
                    echo ""
                    echo "正在停止所有实例..."
                    killed=0
                    for info in "${running_instances[@]}"; do
                        IFS='|' read -r idx c_name pids <<< "$info"
                        for pid in $pids; do
                            kill "$pid" 2>/dev/null && echo "V 已停止 $c_name (PID: $pid)" && killed=$((killed + 1))
                        done
                    done
                    echo ""
                    echo "V 已停止 $killed 个实例"
                    exit 0
                    ;;
                q|Q)
                    exec bash "$0"
                    ;;
                *)
                    found=0
                    for info in "${running_instances[@]}"; do
                        IFS='|' read -r idx c_name pids <<< "$info"
                        if [ "$kill_choice" = "$idx" ]; then
                            found=1
                            echo ""
                            killed=0
                            for pid in $pids; do
                                kill "$pid" 2>/dev/null && echo "V 已停止 $c_name (PID: $pid)" && killed=$((killed + 1))
                            done
                            if [ $killed -eq 0 ]; then
                                echo "X 停止失败"
                                exit 1
                            fi
                            break
                        fi
                    done
                    if [ $found -eq 0 ]; then
                        echo "无效选项或实例未运行"
                        exit 1
                    fi
                    exit 0
                    ;;
            esac
            ;;
    esac
}

if [ -n "$LIST_MODE" ]; then
    execute_command "l"
elif [ -n "$ALL_MODE" ]; then
    execute_command "a"
elif [ -n "$KILL_MODE" ]; then
    execute_command "k"
elif [ ${#POSITIONAL[@]} -gt 0 ]; then
    choice="${POSITIONAL[0]}"
else
    echo "============================================"
    echo "       NanoBOT Gateway 启动器"
    echo "============================================"
    echo ""
    echo "请选择要启动的配置:"
    echo ""

    if [ ${#OPTIONS[@]} -eq 0 ]; then
        echo "  未找到任何配置文件"
        echo "请在 $NANOBOTS_DIR 目录下创建配置文件夹"
        exit 1
    fi

    for idx in "${OPTIONS[@]}"; do
        c_name="${CONFIG_MAP[$idx]}"
        echo "  [$idx] $c_name"
    done
    echo "  [l] 列出所有实例"
    echo "  [a] 启动所有"
    echo "  [k] 停止实例"
    echo "  [q] 退出"
    echo ""
    read -p "请输入选项: " choice
fi

is_valid_choice() {
    for opt in "${OPTIONS[@]}"; do
        if [ "$1" = "$opt" ]; then
            return 0
        fi
    done
    return 1
}

case "$choice" in
    l|L)
        execute_command "l"
        ;;
    a|A)
        execute_command "a"
        ;;
    k|K)
        execute_command "k"
        ;;
    q|Q)
        echo "已退出"
        exit 0
        ;;
    *)
        if is_valid_choice "$choice"; then
            C_NAME="${CONFIG_MAP[$choice]}"
            CONFIG_FILE="${CONFIG_PATH[$C_NAME]}"
            LOG_FILE="${LOG_PATH[$C_NAME]}"
        else
            echo "无效选项"
            exit 1
        fi
        ;;
esac
 
if [ -z "$CONFIG_FILE" ]; then
    echo "错误: 未找到配置"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "X 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

LOG_DIR=$(dirname "$LOG_FILE")
mkdir -p "$LOG_DIR"

echo ""
echo "> 启动配置: $C_NAME"
echo "> 配置文件: $CONFIG_FILE"
echo "> 日志文件: $LOG_FILE"
echo ""

C_NAME=$C_NAME nohup python -m nanobot gateway --config "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &

echo "V $C_NAME 已启动 (PID: $!)"
