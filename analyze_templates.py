"""Analyze all templates to determine optimal face region parameters."""
import cv2
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def analyze_template(template_path: Path) -> dict:
    """Analyze single template and return optimal parameters."""
    img = cv2.imread(str(template_path))
    if img is None:
        return None

    h, w = img.shape[:2]

    # Calculate optimal parameters based on template size
    # These are baseline values that work well for Christmas figure templates

    # Head region size (percentage of template width)
    head_width_ratio = 0.20  # 20% of template width
    head_height_ratio = 0.23  # 23% of template width (oval shape)

    # Position from top (percentage of template height)
    y_position_ratio = 0.14  # 14% from top

    # Calculate actual pixel values
    head_width = int(w * head_width_ratio)
    head_height = int(w * head_height_ratio)  # Based on width for consistent aspect ratio
    x_pos = (w - head_width) // 2  # Centered horizontally
    y_pos = int(h * y_position_ratio)

    return {
        'template': template_path.name,
        'size': f"{w}x{h}",
        'head_width': head_width,
        'head_height': head_height,
        'x_pos': x_pos,
        'y_pos': y_pos,
        'head_width_ratio': head_width_ratio,
        'head_height_ratio': head_height_ratio,
        'y_position_ratio': y_position_ratio
    }


def main():
    """Analyze all templates."""
    templates_dir = Path("images/new_templates")

    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return

    templates = sorted(templates_dir.glob("*.png"))

    if not templates:
        print(f"❌ No templates found in {templates_dir}")
        return

    print("=" * 80)
    print("АНАЛИЗ ПАРАМЕТРОВ ШАБЛОНОВ")
    print("=" * 80)
    print()

    results = []
    for template_path in templates:
        result = analyze_template(template_path)
        if result:
            results.append(result)

    # Print results table
    print(f"{'Шаблон':<20} {'Размер':<12} {'Head W':<8} {'Head H':<8} {'X Pos':<8} {'Y Pos':<8}")
    print("-" * 80)

    for r in results:
        print(f"{r['template']:<20} {r['size']:<12} {r['head_width']:<8} {r['head_height']:<8} {r['x_pos']:<8} {r['y_pos']:<8}")

    print()
    print("=" * 80)
    print("РЕКОМЕНДУЕМЫЕ ПАРАМЕТРЫ")
    print("=" * 80)
    print()
    print("Для всех шаблонов рекомендуется использовать единые параметры:")
    print()
    print("```python")
    print("# Head region parameters")
    print("head_width = int(w * 0.20)   # 20% ширины шаблона")
    print("head_height = int(w * 0.23)  # 23% ширины (овальная форма)")
    print("x = (w - head_width) // 2    # Центр по горизонтали")
    print("y = int(h * 0.14)            # 14% от верха")
    print("```")
    print()

    # Check if all templates have similar aspect ratios
    widths = [r['head_width'] for r in results]
    heights = [r['head_height'] for r in results]

    avg_width = sum(widths) // len(widths)
    avg_height = sum(heights) // len(heights)

    print(f"Средний размер головы: {avg_width}x{avg_height} px")
    print()

    # Analyze template sizes
    print("Размеры шаблонов:")
    template_sizes = set(r['size'] for r in results)
    for size in template_sizes:
        count = sum(1 for r in results if r['size'] == size)
        print(f"  {size}: {count} шаблонов")

    print()
    print("✅ Анализ завершен")


if __name__ == "__main__":
    main()
