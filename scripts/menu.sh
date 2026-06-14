#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

show_menu() {
    clear
    echo ""
    echo "  ╔══════════════════════════════════════════╗"
    echo "  ║        Stack SQL + VS Code               ║"
    echo "  ╠══════════════════════════════════════════╣"
    echo "  ║                                          ║"
    echo "  ║   1)  Levantar entorno                   ║"
    echo "  ║   2)  Parar entorno                      ║"
    echo "  ║   3)  Reset completo (borra datos)       ║"
    echo "  ║   4)  Abrir VS Code                      ║"
    echo "  ║   5)  Abrir psql                         ║"
    echo "  ║   6)  Ver estado del contenedor          ║"
    echo "  ║                                          ║"
    echo "  ║   0)  Salir                              ║"
    echo "  ║                                          ║"
    echo "  ╚══════════════════════════════════════════╝"
    echo ""
}

run_option() {
    local choice="$1"
    echo ""
    case "$choice" in
        1)
            bash "$PROJECT_DIR/scripts/setup.sh"
            ;;
        2)
            make -C "$PROJECT_DIR" stop
            ;;
        3)
            echo "  ⚠️  Esto borrará todos los datos de la base de datos."
            read -rp "  ¿Confirmas? [s/N]: " confirm
            if [[ "$confirm" =~ ^[sS]$ ]]; then
                make -C "$PROJECT_DIR" reset
            else
                echo "  Cancelado."
            fi
            ;;
        4)
            code "$PROJECT_DIR"
            echo "  VS Code abierto."
            ;;
        5)
            make -C "$PROJECT_DIR" psql
            ;;
        6)
            make -C "$PROJECT_DIR" status
            ;;
        0)
            echo "  Hasta luego."
            echo ""
            exit 0
            ;;
        *)
            echo "  Opción no válida. Elige entre 0 y 6."
            ;;
    esac
    echo ""
    read -rp "  Pulsa Enter para volver al menú..."
}

while true; do
    show_menu
    read -rp "  Elige una opción [0-6]: " choice
    run_option "$choice"
done
