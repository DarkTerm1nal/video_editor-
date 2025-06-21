from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, vfx
from moviepy.video.fx.all import resize, crop
import numpy as np
import os

# Настройки
INPUT_DIR = '.'  # Папка с исходными видео
OUTPUT_DIR = 'output'  # Папка для результатов
TEXT_1 = "ТВОЙ ТЕКСТ ghbdf ds fasd adf sdaf asd"  # Первый текст для наложения
TEXT_2 = "ВТОРОЙ ТЕКСТ"  # Второй текст для наложения
TEXT_3 = "3 ТЕКСТ"
FONT_SIZE_1 = 80  # Размер шрифта
FONT_SIZE_2 = 40  # Размер шрифта
FONT_SIZE_3 = 30  # Размер шрифта
FONT_COLOR = 'white'  # Цвет текста
FONT_STROKE_COLOR = 'black'  # Цвет обводки текста
FONT_STROKE_WIDTH = 0  # Ширина обводки текста
AUDIO_FILE = 'audio.mp3'  # Файл со звуком

# Создаем папку для результатов
os.makedirs(OUTPUT_DIR, exist_ok=True)

def add_vinette(clip, factor=0.5):
    """Добавляет виньетку к видео."""
    def apply_vinette(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        X, Y = np.meshgrid(np.linspace(-1, 1, w), np.linspace(-1, 1, h))
        mask = (X**2 + Y**2)**0.5
        vignet = 1 - np.clip(factor * mask, 0, 1)
        vignet = np.dstack([vignet] * 3)
        return np.uint8(frame * vignet)
    return clip.fl(apply_vinette)

def process_video(input_path, output_path, audio_path):
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(input_path):
            print(f"Файл {input_path} не найден!")
            return False

        # Загружаем видео
        clip = VideoFileClip(input_path)

        # Убираем звук из видео
        clip = clip.without_audio()

        # Делаем видео зеркальным
        clip = clip.fx(vfx.mirror_x)

        # Делаем видео темнее
        clip = clip.fx(vfx.colorx, 0.8)

        # Добавляем виньетку
        clip = add_vinette(clip, factor=0.5)

        # Наклон видео на 1 градус
        clip = clip.rotate(angle=0.1)

        # Подгоняем видео под разрешение 1080x1920
        clip_resized = clip.resize(height=1920)

        # Обрезаем видео по ширине, если это необходимо
        if clip_resized.w > 1080:
            x1 = (clip_resized.w - 1080) / 2
            x2 = x1 + 1080
            clip_resized = clip_resized.crop(x1=x1, x2=x2)

        # Устанавливаем ширину текстового блока на 80% от ширины видео
        text_width = int(clip_resized.w * 0.8)
        text_x_position = int(clip_resized.w * 0.10)  # 10% отступ слева

        # Создаем первый текстовый элемент с выравниванием по центру
        txt_clip_1 = TextClip(
            TEXT_1, fontsize=FONT_SIZE_1, color=FONT_COLOR,
            font='Arial', size=(text_width, None),
            stroke_color=FONT_STROKE_COLOR, stroke_width=FONT_STROKE_WIDTH,
            transparent=True, method='caption', align='center'
        )

        # Устанавливаем позицию первого текста с отступом по бокам и сверху
        text_y_position_1 = int(clip_resized.h * 0.10)
        txt_clip_1 = txt_clip_1.set_position((text_x_position, text_y_position_1)).set_duration(clip_resized.duration)

        # Создаем второй текстовый элемент с выравниванием по центру
        txt_clip_2 = TextClip(
            TEXT_2, fontsize=FONT_SIZE_2, color=FONT_COLOR,
            font='Arial', size=(text_width, None),
            stroke_color=FONT_STROKE_COLOR, stroke_width=FONT_STROKE_WIDTH,
            transparent=True, method='caption', align='center'
        )

        # Устанавливаем позицию второго текста на 25% ниже верха
        text_y_position_2 = int(clip_resized.h * 0.25)
        txt_clip_2 = txt_clip_2.set_position((text_x_position, text_y_position_2)).set_duration(clip_resized.duration)

        txt_clip_3 = TextClip(
            TEXT_3, fontsize=FONT_SIZE_3, color=FONT_COLOR,
            font='Arial', size=(text_width, None),
            stroke_color=FONT_STROKE_COLOR, stroke_width=FONT_STROKE_WIDTH,
            transparent=True, method='caption', align='center'
        )

        # Устанавливаем позицию 3тьего текста с отступом по бокам и сверху
        text_y_position_3 = int(clip_resized.h * 0.80)
        txt_clip_3 = txt_clip_3.set_position((text_x_position, text_y_position_3)).set_duration(clip_resized.duration)

        # Накладываем оба текста на видео
        final_clip = CompositeVideoClip([clip_resized, txt_clip_1, txt_clip_2, txt_clip_3])

        # Загружаем аудио
        audio_clip = AudioFileClip(audio_path)

        # Накладываем аудио на видео
        if audio_clip.duration < final_clip.duration:
            # Если аудио короче видео, зацикливаем его
            audio_clip = audio_clip.audio_loop(duration=final_clip.duration)
        else:
            # Обрезаем аудио до длины видео
            audio_clip = audio_clip.subclip(0, final_clip.duration)

        final_clip = final_clip.set_audio(audio_clip)

        # Сохраняем результат
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            logger=None
        )

        # Закрываем клипы
        clip.close()
        final_clip.close()
        audio_clip.close()

        return True
    except Exception as e:
        print(f"Ошибка при обработке {input_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Ищем видеофайлы, исключая временные файлы
video_files = [
    f for f in os.listdir(INPUT_DIR)
    if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')) and not f.startswith('processed_')
]

# Сортируем по числовому значению
video_files.sort()

# Обработка видео
success_count = 0
for video in video_files:
    input_path = os.path.join(INPUT_DIR, video)
    output_path = os.path.join(OUTPUT_DIR, f"processed_{video}")
    print(f"Обработка: {video}")
    if process_video(input_path, output_path, AUDIO_FILE):
        success_count += 1
    print()

print(f"Обработка завершена! Успешно: {success_count}/{len(video_files)}")
