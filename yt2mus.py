import os
import subprocess
from colorama import init, Fore, Style

# Инициализация colorama для цветного текста
init()

# Функция для проверки и установки зависимостей
def install_dependencies():
    # Список пакетов Termux
    termux_packages = ['python', 'mpv', 'yt-dlp']
    # Список Python-модулей
    python_modules = ['youtube-search', 'colorama']

    # Проверка и установка пакетов Termux
    for pkg in termux_packages:
        if os.system(f"command -v {pkg}") != 0:
            print(f"{Fore.YELLOW}Устанавливаю {pkg}...{Style.RESET_ALL}")
            subprocess.run(['pkg', 'install', pkg, '-y'], check=True)

    # Проверка и установка Python-модулей
    for module in python_modules:
        try:
            __import__(module)
        except ImportError:
            print(f"{Fore.YELLOW}Устанавливаю Python-модуль {module}...{Style.RESET_ALL}")
            subprocess.run(['pip', 'install', module], check=True)

    # Установка yt-dlp отдельно через pip, так как это Python-пакет
    try:
        import yt_dlp
    except ImportError:
        print(f"{Fore.YELLOW}Устанавливаю Python-модуль yt-dlp...{Style.RESET_ALL}")
        subprocess.run(['pip', 'install', 'yt-dlp'], check=True)

# Импорт youtube_search после установки зависимостей
from youtube_search import YoutubeSearch

# Поиск треков через YouTube
def search_tracks(query, page=1):
    limit = 50
    offset = (page - 1) * limit
    search = YoutubeSearch(query, max_results=limit + offset).to_dict()
    results = search[offset:offset + limit]
    tracks = []
    for video in results:
        tracks.append({
            'title': video['title'],
            'url': f"https://www.youtube.com{video['url_suffix']}",
            'artist': video['channel']  # Канал как аналог исполнителя
        })
    return tracks

# Вывод списка треков
def display_tracks(tracks, page):
    start_index = (page - 1) * 50
    print(f"\n{Fore.BLUE}=== Страница {page} ==={Style.RESET_ALL}\n")
    for i, track in enumerate(tracks, start_index + 1):
        artist = track.get('artist', 'Неизвестный исполнитель')
        title = track.get('title', 'Без названия')
        print(f"{Fore.GREEN}{i}. {artist} - {title}{Style.RESET_ALL}")
    print()

# Воспроизведение трека
def play_track(track_url):
    try:
        print(f"{Fore.YELLOW}Управление: Пробел - пауза/возобновление, q - остановить{Style.RESET_ALL}")
        subprocess.run(['mpv', '--no-video', track_url], check=True)
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Ошибка воспроизведения: {e}{Style.RESET_ALL}")

# Скачивание трека
def download_track(track_url, filename):
    try:
        print(f"{Fore.YELLOW}Скачивание началось...{Style.RESET_ALL}")
        subprocess.run(['yt-dlp', '-x', '--audio-format', 'mp3', '-o', f"{filename}.mp3", '--progress', track_url], check=True)
        print(f"{Fore.GREEN}Трек сохранён как {filename}.mp3{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Ошибка скачивания: {e}{Style.RESET_ALL}")

# Основная логика
def main():
    # Установка всех зависимостей при первом запуске
    print(f"{Fore.BLUE}=== Проверка и установка зависимостей ==={Style.RESET_ALL}")
    install_dependencies()
    print(f"{Fore.GREEN}Все зависимости установлены!{Style.RESET_ALL}\n")

    print(f"{Fore.BLUE}=== Поиск музыки через YouTube ==={Style.RESET_ALL}\n")
    
    while True:
        query = input(f"{Fore.CYAN}Введите название трека или имя исполнителя (или 'exit' для выхода): {Style.RESET_ALL}")
        if query.lower() == 'exit':
            print(f"{Fore.BLUE}Программа завершена.{Style.RESET_ALL}")
            break

        current_page = 1
        tracks = search_tracks(query, current_page)

        if not tracks:
            print(f"{Fore.RED}Треки не найдены.{Style.RESET_ALL}")
            continue

        # Внутренний цикл для работы с текущим поиском
        while True:
            display_tracks(tracks, current_page)
            command = input(f"{Fore.CYAN}Введите команду ('номер L' - прослушать, 'номер D' - скачать, 'номер' - страница, 'r' - новый поиск, 'exit' - выход): {Style.RESET_ALL}").strip().lower()

            if command == 'exit':
                print(f"{Fore.BLUE}Программа завершена.{Style.RESET_ALL}")
                return
            elif command == 'r':
                print(f"{Fore.YELLOW}Сброс поиска...{Style.RESET_ALL}")
                break

            try:
                parts = command.split()
                if len(parts) == 1:  # Переключение страницы
                    new_page = int(parts[0])
                    if new_page < 1:
                        print(f"{Fore.RED}Номер страницы должен быть больше 0.{Style.RESET_ALL}")
                        continue
                    current_page = new_page
                    tracks = search_tracks(query, current_page)
                    if not tracks:
                        print(f"{Fore.RED}На этой странице больше нет треков.{Style.RESET_ALL}")
                        current_page -= 1
                        tracks = search_tracks(query, current_page)
                    continue

                elif len(parts) == 2:  # Команда с действием
                    num, action = int(parts[0]), parts[1]
                    track_index = num - 1 - (current_page - 1) * 50
                    
                    if not (0 <= track_index < len(tracks)):
                        print(f"{Fore.RED}Номер должен быть в пределах текущей страницы ({1 + (current_page - 1) * 50} - {current_page * 50}).{Style.RESET_ALL}")
                        continue

                    track = tracks[track_index]
                    track_url = track['url']
                    filename = f"{track['artist']} - {track['title']}".replace('/', '_').replace(':', '_')

                    if action in ['l', 'L']:
                        print(f"{Fore.YELLOW}Воспроизвожу: {track['artist']} - {track['title']}{Style.RESET_ALL}")
                        play_track(track_url)
                        print()
                    elif action in ['d', 'D']:
                        print(f"{Fore.YELLOW}Скачиваю: {track['artist']} - {track['title']}{Style.RESET_ALL}")
                        download_track(track_url, filename)
                        print()
                    else:
                        print(f"{Fore.RED}Неверная команда. Используйте 'L' для прослушивания или 'D' для скачивания.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Неверный формат команды.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Введите корректную команду (например, '3 L', '15 D', '2' или 'r').{Style.RESET_ALL}")
            except IndexError:
                print(f"{Fore.RED}Трек с таким номером не найден.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
