"""Visualize face regions on all templates for verification."""
import cv2
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def visualize_template(template_path: Path, output_dir: Path):
    """Visualize face region on template."""
    img = cv2.imread(str(template_path))
    if img is None:
        print(f"❌ Не удалось загрузить: {template_path}")
        return None

    h, w = img.shape[:2]

    # Same parameters as in template_generator.py
    head_width = int(w * 0.20)   # 20% ширины шаблона
    head_height = int(w * 0.23)  # 23% ширины для учета волос
    x = (w - head_width) // 2    # Центр по горизонтали
    y = int(h * 0.14)            # 14% от верха

    # Create visualization
    vis = img.copy()

    # Draw rectangle
    cv2.rectangle(vis, (x, y), (x + head_width, y + head_height), (0, 255, 0), 2)

    # Draw center lines
    center_x = x + head_width // 2
    center_y = y + head_height // 2

    # Vertical center line
    cv2.line(vis, (center_x, 0), (center_x, h), (255, 0, 0), 1)
    # Horizontal center line
    cv2.line(vis, (0, center_y), (w, center_y), (255, 0, 0), 1)

    # Draw ellipse (actual face region)
    cv2.ellipse(vis, (center_x, center_y), (head_width // 2, head_height // 2), 0, 0, 360, (0, 0, 255), 2)

    # Add text info
    info_text = f"{template_path.stem} | {w}x{h} | Face: {head_width}x{head_height} at ({x},{y})"
    cv2.putText(vis, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(vis, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

    # Save
    output_path = output_dir / f"{template_path.stem}_visualization.jpg"
    cv2.imwrite(str(output_path), vis, [cv2.IMWRITE_JPEG_QUALITY, 95])

    return {
        'template': template_path.name,
        'size': f"{w}x{h}",
        'face_region': f"{head_width}x{head_height}",
        'position': f"({x},{y})",
        'output': output_path.name
    }


def main():
    """Visualize all templates."""
    templates_dir = Path("images/new_templates")
    output_dir = Path("template_visualizations")
    output_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print("ВИЗУАЛИЗАЦИЯ FACE REGIONS НА ВСЕХ ШАБЛОНАХ")
    print("=" * 80)
    print()

    if not templates_dir.exists():
        print(f"❌ Папка шаблонов не найдена: {templates_dir}")
        return

    templates = sorted(templates_dir.glob("*.png"))

    if not templates:
        print(f"❌ Шаблоны не найдены в {templates_dir}")
        return

    print(f"📁 Папка шаблонов: {templates_dir}")
    print(f"📁 Папка результатов: {output_dir}")
    print(f"📊 Найдено шаблонов: {len(templates)}")
    print()

    results = []

    for idx, template_path in enumerate(templates, 1):
        print(f"[{idx}/{len(templates)}] Обработка {template_path.name}...", end=" ")

        result = visualize_template(template_path, output_dir)

        if result:
            results.append(result)
            print("✅")
        else:
            print("❌")

    print()
    print("=" * 80)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 80)
    print()

    print(f"{'Шаблон':<20} {'Размер':<10} {'Face Region':<15} {'Position':<12} {'Выход':<30}")
    print("-" * 80)

    for r in results:
        print(f"{r['template']:<20} {r['size']:<10} {r['face_region']:<15} {r['position']:<12} {r['output']:<30}")

    print()
    print(f"✅ Создано визуализаций: {len(results)}")
    print(f"📁 Сохранено в: {output_dir.absolute()}")
    print()
    print("Проверьте изображения для оценки корректности позиционирования:")
    print("  🟢 Зеленый прямоугольник - границы face region")
    print("  🔴 Красный эллипс - фактическая область вставки лица")
    print("  🔵 Синие линии - центр face region")


if __name__ == "__main__":
    main()
