import os
import subprocess
import sys
import argparse
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

# Константы
DEP_FLAG = Path(".dependencies_installed")
DOWNLOAD_DIR = Path("music")

class MusicDownloader:
    def __init__(self):
        self.ensure_dirs()
        DOWNLOAD_DIR.mkdir(exist_ok=True)

    def ensure_dirs(self):
        """Создаёт необходимые директории"""
        pass

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Очистка имени файла"""
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '_')
        return name.strip()[:200]

    def install_dependencies(self):
        """Установка зависимостей (только один раз)"""
        if DEP_FLAG.exists():
            return

        print(f"{Fore.BLUE}=== Первый запуск: установка зависимостей ==={Style.RESET_ALL}")
        
        termux_packages = ['python', 'mpv', 'yt-dlp', 'ffmpeg']
        python_modules = ['youtube-search', 'colorama']

        # Проверка Termux-пакетов (исправлено для Termux)
        for pkg in termux_packages:
            try:
                result = subprocess.run(['which', pkg], capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"{Fore.YELLOW}Устанавливаю {pkg}...{Style.RESET_ALL}")
                    subprocess.run(['pkg', 'install', pkg, '-y'], check=True)
            except Exception:
                # Fallback
                print(f"{Fore.YELLOW}Устанавливаю {pkg}...{Style.RESET_ALL}")
                subprocess.run(['pkg', 'install', pkg, '-y'], check=True)

        for module in python_modules:
            try:
                __import__(module)
            except ImportError:
                print(f"{Fore.YELLOW}Устанавливаю Python-модуль {module}...{Style.RESET_ALL}")
                subprocess.run([sys.executable, '-m', 'pip', 'install', module], check=True)

        # yt-dlp
        try:
            import yt_dlp
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp', '--upgrade'], check=True)

        # Обновляем yt-dlp
        print(f"{Fore.YELLOW}Обновляем yt-dlp до последней версии...{Style.RESET_ALL}")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'yt-dlp', '--upgrade'], check=True)

        DEP_FLAG.touch()
        print(f"{Fore.GREEN}✅ Зависимости успешно установлены!{Style.RESET_ALL}\n")

    def search_tracks(self, query: str, page: int = 1, limit: int = 20):
        from youtube_search import YoutubeSearch
        offset = (page - 1) * limit
        search = YoutubeSearch(query, max_results=limit + offset).to_dict()
        results = search[offset:offset + limit]
        
        return [{
            'title': video['title'],
            'url': f"https://www.youtube.com{video['url_suffix']}",
            'artist': video.get('channel', 'Неизвестный')
        } for video in results]

    def display_tracks(self, tracks, page):
        print(f"\n{Fore.BLUE}=== Страница {page} ==={Style.RESET_ALL}\n")
        for i, track in enumerate(tracks, 1):
            print(f"{Fore.GREEN}{i}. {track['artist']} - {track['title']}{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Команды: [номер]L — слушать, [номер]D — скачать, N — страница, R — новый поиск, Q — выход{Style.RESET_ALL}")

    def play_track(self, url: str):
        try:
            print(f"{Fore.YELLOW}▶ Воспроизведение... (q — остановить){Style.RESET_ALL}")
            subprocess.run(['mpv', '--no-video', '--quiet', url], check=True)
        except Exception as e:
            print(f"{Fore.RED}Ошибка воспроизведения: {e}{Style.RESET_ALL}")

    def download_track(self, url: str, filename: str):
        try:
            filepath = DOWNLOAD_DIR / f"{filename}.mp3"
            print(f"{Fore.YELLOW}⬇ Скачивание в {filepath}...{Style.RESET_ALL}")
            
            subprocess.run([
                'yt-dlp', '-x', '--audio-format', 'mp3',
                '--progress', '-o', str(filepath), url
            ], check=True)
            
            print(f"{Fore.GREEN}✅ Скачано: {filepath}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Ошибка скачивания: {e}{Style.RESET_ALL}")

    def run_interactive(self):
        self.install_dependencies()
        print(f"{Fore.BLUE}=== YouTube Music Downloader ==={Style.RESET_ALL}\n")

        while True:
            query = input(f"{Fore.CYAN}Поиск (или 'q' для выхода): {Style.RESET_ALL}").strip()
            if query.lower() in ['q', 'exit', 'quit']:
                break

            page = 1
            while True:
                tracks = self.search_tracks(query, page)
                if not tracks:
                    print(f"{Fore.RED}Ничего не найдено.{Style.RESET_ALL}")
                    break

                self.display_tracks(tracks, page)
                cmd = input(f"{Fore.CYAN}Команда: {Style.RESET_ALL}").strip().lower()

                if cmd in ['q', 'exit']:
                    return
                elif cmd == 'r':
                    break
                elif cmd.isdigit():
                    page = int(cmd)
                    continue

                try:
                    parts = cmd.split()
                    num = int(parts[0])
                    action = parts[1] if len(parts) > 1 else 'l'
                    
                    track = tracks[num - 1]
                    filename = self.sanitize_filename(f"{track['artist']} - {track['title']}")

                    if action in ['l', 'play']:
                        self.play_track(track['url'])
                    elif action in ['d', 'download']:
                        self.download_track(track['url'], filename)
                except Exception:
                    print(f"{Fore.RED}Неверная команда. Пример: 3d или 5l{Style.RESET_ALL}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Music Downloader")
    parser.add_argument('-s', '--search', help="Поисковый запрос")
    parser.add_argument('-d', '--download', help="Скачать по номеру после поиска")
    args = parser.parse_args()

    app = MusicDownloader()
    
    if args.search:
        print("Прямой режим пока в разработке. Запускаю интерактивный...")
    
    app.run_interactive()
