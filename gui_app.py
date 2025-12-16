import asyncio
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
import sys
import os

sys.path.append(os.getcwd())

from gamdl.api import AppleMusicApi, ItunesApi
from gamdl.downloader import (
    AppleMusicBaseDownloader,
    AppleMusicDownloader,
    AppleMusicMusicVideoDownloader,
    AppleMusicSongDownloader,
    AppleMusicUploadedVideoDownloader,
    DownloadMode,
    RemuxMode,
    CoverFormat,
    GamdlError,
    DownloadItem,
)
from gamdl.interface import (
    AppleMusicInterface,
    AppleMusicSongInterface,
    AppleMusicMusicVideoInterface,
    AppleMusicUploadedVideoInterface,
    SongCodec,
    SyncedLyricsFormat,
    MusicVideoCodec,
    MusicVideoResolution,
    UploadedVideoQuality,
)
from gamdl.cli.utils import CustomLoggerFormatter
from gamdl.cli.constants import X_NOT_IN_PATH

# 歌曲编码选项映射
SONG_CODEC_OPTIONS = {
    "aac-legacy - AAC 256kbps 44.1kHz (稳定)": "aac-legacy",
    "aac-he-legacy - AAC-HE 64kbps 44.1kHz (稳定)": "aac-he-legacy",
    "aac - AAC 256kbps up to 48kHz (实验性)": "aac",
    "aac-he - AAC-HE 64kbps up to 48kHz (实验性)": "aac-he",
    "aac-binaural - AAC 256kbps binaural (实验性)": "aac-binaural",
    "aac-downmix - AAC 256kbps downmix (实验性)": "aac-downmix",
    "aac-he-binaural - AAC-HE 64kbps binaural (实验性)": "aac-he-binaural",
    "aac-he-downmix - AAC-HE 64kbps downmix (实验性)": "aac-he-downmix",
    "atmos - Dolby Atmos 768kbps (实验性)": "atmos",
    "ac3 - AC3 640kbps (实验性)": "ac3",
    "alac - ALAC up to 24-bit/192kHz (不支持)": "alac"
}

# 封面格式选项映射
COVER_FORMAT_OPTIONS = {
    "jpg": CoverFormat.JPG,
    "png": CoverFormat.PNG,
    "raw (需启用保存封面)": CoverFormat.RAW
}

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

class GamdlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gamdl GUI")
        self.root.geometry("900x750")
        
        # 变量
        self.urls_var = tk.StringVar()
        self.cookies_path_var = tk.StringVar()
        self.wvd_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar(value=str(Path.home() / "Downloads" / "Gamdl"))
        self.temp_path_var = tk.StringVar()
        
        # 默认选中第一个选项
        self.song_codec_var = tk.StringVar(value=list(SONG_CODEC_OPTIONS.keys())[0])
        self.synced_lyrics_format_var = tk.StringVar(value="lrc")
        self.language_var = tk.StringVar(value="zh-CN")
        self.cover_format_var = tk.StringVar(value="jpg")
        
        self.save_cover_var = tk.BooleanVar(value=True)
        self.save_playlist_var = tk.BooleanVar(value=False)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.no_synced_lyrics_var = tk.BooleanVar(value=False)
        
        self.setup_ui()
        self.setup_logging()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. URL 输入
        url_frame = ttk.LabelFrame(main_frame, text="下载链接 (每行一个)", padding="5")
        url_frame.pack(fill=tk.X, pady=5)
        
        self.url_text = tk.Text(url_frame, height=4)
        self.url_text.pack(fill=tk.X)
        
        # 2. 路径配置
        path_frame = ttk.LabelFrame(main_frame, text="路径设置", padding="5")
        path_frame.pack(fill=tk.X, pady=5)
        
        self.create_file_input(path_frame, "Cookies 文件 (.txt):", self.cookies_path_var, 0, file_type="file")
        self.create_file_input(path_frame, "WVD 文件 (.wvd) [可选]:", self.wvd_path_var, 1, file_type="file")
        self.create_file_input(path_frame, "保存目录:", self.output_path_var, 2, file_type="dir")
        
        # 3. 选项配置
        options_frame = ttk.LabelFrame(main_frame, text="下载选项", padding="5")
        options_frame.pack(fill=tk.X, pady=5)
        
        # 第一行
        ttk.Label(options_frame, text="歌曲编码:").grid(row=0, column=0, sticky=tk.W, padx=5)
        codec_combo = ttk.Combobox(options_frame, textvariable=self.song_codec_var, state="readonly", width=40)
        codec_combo['values'] = list(SONG_CODEC_OPTIONS.keys())
        codec_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(options_frame, text="歌词格式:").grid(row=0, column=2, sticky=tk.W, padx=5)
        lyrics_combo = ttk.Combobox(options_frame, textvariable=self.synced_lyrics_format_var, state="readonly", width=10)
        lyrics_combo['values'] = [e.value for e in SyncedLyricsFormat]
        lyrics_combo.grid(row=0, column=3, sticky=tk.W, padx=5)

        # 第二行
        ttk.Label(options_frame, text="元数据语言:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        lang_combo = ttk.Combobox(options_frame, textvariable=self.language_var, state="readonly", width=10)
        lang_combo['values'] = ["zh-CN", "en-US", "ja-JP", "ko-KR"]
        lang_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(options_frame, text="封面格式:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        cover_combo = ttk.Combobox(options_frame, textvariable=self.cover_format_var, state="readonly", width=20)
        cover_combo['values'] = list(COVER_FORMAT_OPTIONS.keys())
        cover_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 第三行复选框
        check_frame = ttk.Frame(options_frame)
        check_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(check_frame, text="保存封面", variable=self.save_cover_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(check_frame, text="保存播放列表", variable=self.save_playlist_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(check_frame, text="覆盖已存在文件", variable=self.overwrite_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(check_frame, text="不下载歌词", variable=self.no_synced_lyrics_var).pack(side=tk.LEFT, padx=5)

        # 4. 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="开始下载", command=self.start_download)
        self.start_btn.pack(side=tk.RIGHT, padx=5)

        # 5. 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_file_input(self, parent, label_text, var, row, file_type="file"):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky=tk.EW, padx=5, pady=2)
        
        if file_type == "file":
            cmd = lambda: var.set(filedialog.askopenfilename())
        else:
            cmd = lambda: var.set(filedialog.askdirectory())
            
        ttk.Button(parent, text="浏览...", command=cmd).grid(row=row, column=2, padx=5, pady=2)
        parent.columnconfigure(1, weight=1)

    def setup_logging(self):
        self.logger = logging.getLogger("gamdl")
        self.logger.setLevel(logging.INFO)
        
        # 清除现有的 handlers
        self.logger.handlers = []
        
        handler = TextHandler(self.log_text)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # 同时也输出到控制台，方便调试
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def start_download(self):
        urls = self.url_text.get("1.0", tk.END).strip().splitlines()
        urls = [u.strip() for u in urls if u.strip()]
        
        if not urls:
            messagebox.showwarning("提示", "请输入下载链接")
            return
            
        cookies_path = self.cookies_path_var.get()
        if not cookies_path or not os.path.exists(cookies_path):
            messagebox.showwarning("提示", "请选择有效的 Cookies 文件")
            return

        self.start_btn.config(state="disabled")
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        
        # 在新线程中运行异步任务
        threading.Thread(target=self.run_async_task, args=(urls,), daemon=True).start()

    def run_async_task(self, urls):
        try:
            asyncio.run(self.download_logic(urls))
        except Exception as e:
            self.logger.error(f"发生未捕获的异常: {e}", exc_info=True)
        finally:
            self.root.after(0, lambda: self.start_btn.config(state="normal"))

    async def download_logic(self, urls):
        try:
            # 收集参数
            cookies_path = self.cookies_path_var.get()
            wvd_path = self.wvd_path_var.get() if self.wvd_path_var.get() else None
            output_path = self.output_path_var.get()
            temp_path = self.temp_path_var.get() if self.temp_path_var.get() else None
            
            # 解析选项
            song_codec_str = SONG_CODEC_OPTIONS[self.song_codec_var.get()]
            song_codec = SongCodec(song_codec_str)
            
            synced_lyrics_format = SyncedLyricsFormat(self.synced_lyrics_format_var.get())
            language = self.language_var.get()
            
            cover_format_key = self.cover_format_var.get()
            cover_format = COVER_FORMAT_OPTIONS[cover_format_key]
            
            # 检查 raw 格式是否启用了 save_cover
            if cover_format == CoverFormat.RAW and not self.save_cover_var.get():
                self.logger.warning("注意：选择了 RAW 封面格式但未启用保存封面，已自动启用保存封面。")
                self.save_cover_var.set(True)

            # 初始化 API
            self.logger.info(f"正在初始化 Apple Music API (语言: {language})...")
            apple_music_api = await AppleMusicApi.create_from_netscape_cookies(
                cookies_path=cookies_path,
                language=language,
            )
            
            itunes_api = ItunesApi(
                apple_music_api.storefront,
                apple_music_api.language,
            )
            
            if not apple_music_api.active_subscription:
                self.logger.critical("未检测到有效的 Apple Music 订阅，无法下载。")
                return

            # 初始化 Interface
            interface = AppleMusicInterface(apple_music_api, itunes_api)
            song_interface = AppleMusicSongInterface(interface)
            music_video_interface = AppleMusicMusicVideoInterface(interface)
            uploaded_video_interface = AppleMusicUploadedVideoInterface(interface)
            
            # 初始化 Downloader
            base_downloader = AppleMusicBaseDownloader(
                output_path=str(Path(output_path)),
                temp_path=str(Path(temp_path)) if temp_path else ".",
                wvd_path=str(Path(wvd_path)) if wvd_path else None,
                overwrite=self.overwrite_var.get(),
                save_cover=self.save_cover_var.get(),
                save_playlist=self.save_playlist_var.get(),
                # 其他参数使用默认值或根据需要添加
                nm3u8dlre_path="N_m3u8DL-RE",
                mp4decrypt_path="mp4decrypt",
                ffmpeg_path="ffmpeg",
                mp4box_path="MP4Box",
                amdecrypt_path="amdecrypt",
                download_mode=DownloadMode.YTDLP, # 默认使用 YTDLP
                remux_mode=RemuxMode.FFMPEG,
                cover_format=cover_format,
                cover_size=1200,
                truncate=50,
            )
            
            song_downloader = AppleMusicSongDownloader(
                base_downloader=base_downloader,
                interface=song_interface,
                codec=song_codec,
                synced_lyrics_format=synced_lyrics_format,
                no_synced_lyrics=self.no_synced_lyrics_var.get(),
                synced_lyrics_only=False,
            )
            
            music_video_downloader = AppleMusicMusicVideoDownloader(
                base_downloader=base_downloader,
                interface=music_video_interface,
                codec_priority=[MusicVideoCodec.H264], # 默认
                remux_format=None,
                resolution=MusicVideoResolution.R1080P,
            )
            
            uploaded_video_downloader = AppleMusicUploadedVideoDownloader(
                base_downloader=base_downloader,
                interface=uploaded_video_interface,
                quality=UploadedVideoQuality.BEST,
            )
            
            downloader = AppleMusicDownloader(
                interface=interface,
                base_downloader=base_downloader,
                song_downloader=song_downloader,
                music_video_downloader=music_video_downloader,
                uploaded_video_downloader=uploaded_video_downloader,
            )
            
            # 检查外部工具
            # 这里简化处理，假设用户已经配置好环境变量，或者在打包时包含这些工具
            
            # 开始下载
            error_count = 0
            for i, url in enumerate(urls, 1):
                self.logger.info(f"正在处理 ({i}/{len(urls)}): {url}")
                try:
                    url_info = downloader.get_url_info(url)
                    if not url_info:
                        self.logger.warning(f"无法解析 URL: {url}")
                        continue
                        
                    download_queue = await downloader.get_download_queue(url_info)
                    if not download_queue:
                        self.logger.warning(f"未找到可下载的媒体: {url}")
                        continue
                        
                    for j, item in enumerate(download_queue, 1):
                        title = item.media_metadata["attributes"]["name"]
                        self.logger.info(f"正在下载 [{j}/{len(download_queue)}]: {title}")
                        try:
                            await downloader.download(item)
                            self.logger.info(f"下载完成: {title}")
                        except Exception as e:
                            self.logger.error(f"下载失败 {title}: {e}")
                            error_count += 1
                            
                except Exception as e:
                    self.logger.error(f"处理 URL 时出错 {url}: {e}")
                    error_count += 1
            
            self.logger.info(f"所有任务完成，错误数: {error_count}")
            
        except Exception as e:
            self.logger.error(f"初始化或运行时发生错误: {e}", exc_info=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = GamdlGUI(root)
    root.mainloop()
