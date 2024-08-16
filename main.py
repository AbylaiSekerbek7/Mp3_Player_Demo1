import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, simpledialog, PhotoImage
import pygame
import os
import sqlite3


class MP3Player:
    def __init__(self, root):
        self.root = root
        self.root.title("MP3 Player")
        self.root.geometry("800x600")

        # init pygame
        # pygame.mixer.init()

        # Connection to SQLite
        self.conn = sqlite3.connect("music_player.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

        # Interface
        self.playlist = []
        self.current_index = 0
        self.is_paused = False
        self.repeat_mode = "none"  # 'none', 'single', 'all'

        self.create_widgets()
        self.load_playlists()
        self.load_favorites()

    def create_tables(self):
        # Table for playlists, songs, favorite songs
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_songs (
            id INTEGER PRIMARY KEY,
            playlist_id INTEGER,
            song_path TEXT,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY,
            song_path TEXT
        )
        """)

        self.conn.commit()

    def create_widgets(self):
        # Виджеты интерфейса
        self.current_song_label = tk.Label(self.root, text="No song playing", font=("Arial", 14))
        self.current_song_label.pack(pady=10)

        self.song_listbox = Listbox(self.root, selectmode=tk.SINGLE, bg="lightgray", fg="black", width=60, height=10)
        self.song_listbox.pack(pady=20)

        controls_frame = tk.Frame(self.root)
        controls_frame.pack()

        self.prev_img = PhotoImage(file="images/prev_btn.png")

        prev_button = tk.Button(controls_frame, text="Previous", image=self.prev_img, command=self.play_previous)
        prev_button.grid(row=0, column=0, padx=10)

        self.play_img = PhotoImage(file="images/start_btn.png")

        play_button = tk.Button(controls_frame, text="Start", image=self.play_img, command=self.play_pause_song)
        play_button.grid(row=0, column=1, padx=10)

        self.stop_img = PhotoImage(file="images/stop_btn.png")

        stop_button = tk.Button(controls_frame, text="Stop", image=self.stop_img, command=self.stop_song)
        stop_button.grid(row=0, column=2, padx=10)

        self.next_img = PhotoImage(file="images/next_btn.png")

        next_button = tk.Button(controls_frame, text="Next", image=self.next_img, command=self.play_next)
        next_button.grid(row=0, column=3, padx=10)

        self.rep_img = PhotoImage(file="images/repeat_mode.png")
        self.sequ_img = PhotoImage(file="images/sequ_mode.png")
        self.none_img = PhotoImage(file="images/none_mode.png")

        self.repeat_button = tk.Button(controls_frame, text="Repeat Mode", image=self.none_img, command=self.change_repeat_mode)
        self.repeat_button.grid(row=0, column=4, padx=10)

        # Кнопки для управления плейлистами и избранными песнями
        playlist_button = tk.Button(self.root, text="Add Playlist", command=self.add_playlist)
        playlist_button.pack(pady=10)

        load_button = tk.Button(self.root, text="Load Songs", command=self.load_songs)
        load_button.pack(pady=10)

        favorites_button = tk.Button(self.root, text="Add to Favorites", command=self.add_to_favorites)
        favorites_button.pack()

        # Списки для плейлистов и любимых песен
        playlists_frame = tk.Frame(self.root)
        playlists_frame.pack(side=tk.LEFT, padx=20)

        tk.Label(playlists_frame, text="Playlists", font=("Arial", 12)).pack()
        self.playlists_listbox = Listbox(playlists_frame, bg="lightgray", fg="black", width=20, height=10)
        self.playlists_listbox.pack(pady=10)
        self.playlists_listbox.bind("<<ListboxSelect>>", self.load_playlist_songs)

        favorites_frame = tk.Frame(self.root)
        favorites_frame.pack(side=tk.RIGHT, padx=20)

        tk.Label(favorites_frame, text="Favorites", font=("Arial", 12)).pack()
        self.favorites_listbox = Listbox(favorites_frame, bg="lightgray", fg="black", width=20, height=10)
        self.favorites_listbox.pack(pady=10)

    def load_songs(self):
        song_paths = filedialog.askopenfilenames(filetypes=[("MP3 Files", "*.mp3")])
        for song in song_paths:
            self.song_listbox.insert(tk.END, os.path.basename(song))
            self.playlist.append(song)

    def play_pause_song(self):
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
        else:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
                self.is_paused = True
            else:
                self.play_song()

    def play_song(self):
        if self.playlist:
            pygame.mixer.music.load(self.playlist[self.current_index])
            pygame.mixer.music.play(loops=0)
            self.current_song_label.config(text=f"Playing: {os.path.basename(self.playlist[self.current_index])}")
            pygame.mixer.music.set_endevent(pygame.USEREVENT)  # Для обработки окончания песни
            self.root.after(100, self.check_song_end)  # Проверяем окончание песни

    def check_song_end(self):
        if not pygame.mixer.music.get_busy():
            if self.repeat_mode == "single":
                self.play_song()  # Повторяем песню
            elif self.repeat_mode == "all":
                self.play_next()  # Переходим к следующей
            else:
                self.current_song_label.config(text="No song playing")
        else:
            self.root.after(100, self.check_song_end)

    def stop_song(self):
        pygame.mixer.music.stop()
        self.current_song_label.config(text="No song playing")

    def play_next(self):
        if self.repeat_mode != "single":
            self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_song()

    def play_previous(self):
        if self.playlist:  # Проверяем, что плейлист не пуст
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_song()
        else:
            messagebox.showwarning("Warning", "Playlist is empty!")

    def change_repeat_mode(self):
        if self.repeat_mode == "none":
            self.repeat_mode = "single"
            self.repeat_button.config(image=self.rep_img)
            messagebox.showinfo("Repeat Mode", "Single song repeat enabled")
        elif self.repeat_mode == "single":
            self.repeat_mode = "all"
            self.repeat_button.config(image=self.sequ_img)
            messagebox.showinfo("Repeat Mode", "All songs repeat enabled")
        else:
            self.repeat_mode = "none"
            self.repeat_button.config(image=self.none_img)
            messagebox.showinfo("Repeat Mode", "Repeat disabled")

    def add_playlist(self):
        playlist_name = simpledialog.askstring("Playlist Name", "Enter the name of the playlist:")
        if playlist_name:
            self.cursor.execute("INSERT INTO playlists (name) VALUES (?)", (playlist_name,))
            playlist_id = self.cursor.lastrowid
            for song in self.playlist:
                self.cursor.execute("INSERT INTO playlist_songs (playlist_id, song_path) VALUES (?, ?)", (playlist_id, song))
            self.conn.commit()
            self.playlists_listbox.insert(tk.END, playlist_name)
            messagebox.showinfo("Playlist", f"Playlist '{playlist_name}' added successfully!")

    def load_playlists(self):
        self.playlists_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT name FROM playlists")
        playlists = self.cursor.fetchall()
        for playlist in playlists:
            self.playlists_listbox.insert(tk.END, playlist[0])

    def load_playlist_songs(self, event):
        selected_playlist = self.playlists_listbox.get(tk.ACTIVE)
        self.cursor.execute("SELECT id FROM playlists WHERE name = ?", (selected_playlist,))
        playlist_id = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT song_path FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
        songs = self.cursor.fetchall()

        self.song_listbox.delete(0, tk.END)
        self.playlist = []
        for song in songs:
            self.song_listbox.insert(tk.END, os.path.basename(song[0]))
            self.playlist.append(song[0])

    def add_to_favorites(self):
        if self.playlist:
            current_song = self.playlist[self.current_index]
            self.cursor.execute("INSERT INTO favorites (song_path) VALUES (?)", (current_song,))
            self.conn.commit()
            self.load_favorites()
            messagebox.showinfo("Favorites", "Song added to favorites!")
        else:
            messagebox.showwarning("No Songs Loaded", "Please load songs to add to favorites.")

    def load_favorites(self):
        self.favorites_listbox.delete(0, tk.END)
        self.cursor.execute("SELECT song_path FROM favorites")
        favorites = self.cursor.fetchall()
        for song in favorites:
            self.favorites_listbox.insert(tk.END, os.path.basename(song[0]))

    def on_close(self):
        pygame.mixer.music.stop()
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    player = MP3Player(root)
    root.protocol("WM_DELETE_WINDOW", player.on_close)
    root.mainloop()
