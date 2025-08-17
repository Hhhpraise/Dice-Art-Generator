import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Scale
from PIL import Image, ImageTk, ImageDraw, ImageEnhance
import numpy as np
import os
import json
from datetime import datetime


class EnhancedDiceArtGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Dice Art Generator")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2c3e50")

        # Configure styles
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#2c3e50")
        self.style.configure("TLabel", background="#2c3e50", foreground="#ecf0f1")
        self.style.configure("TButton", background="#3498db", foreground="#2c3e50")
        self.style.map("TButton", background=[('active', '#2980b9')])
        self.style.configure("TScale", background="#2c3e50")
        self.style.configure("TEntry", fieldbackground="#34495e")
        self.style.configure("Horizontal.TScale", background="#2c3e50")
        self.style.configure("TCombobox", fieldbackground="#34495e")

        # Variables
        self.image_path = ""
        self.dice_grid = None
        self.total_dice = 0
        self.dice_width = tk.IntVar(value=30)
        self.dice_size = tk.IntVar(value=20)  # Size of each die in preview
        self.dice_color = tk.StringVar(value="white")
        self.brightness = tk.DoubleVar(value=1.0)
        self.contrast = tk.DoubleVar(value=1.0)
        self.preview_size = 300
        self.dice_values = [1, 2, 3, 4, 5, 6]
        self.dice_colors = {
            "white": ("#e0e0e0", "#2c3e50"),
            "black": ("#2c3e50", "#e0e0e0"),
            "wood": ("#d2b48c", "#2c3e50"),
            "red": ("#e74c3c", "#f9e9e8"),
            "blue": ("#3498db", "#eaf4fc")
        }
        self.current_project = None

        # Create main frames
        self.control_frame = ttk.Frame(root, padding=10)
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.preview_frame = ttk.Frame(root, padding=10)
        self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Control panel widgets
        ttk.Label(self.control_frame, text="ENHANCED DICE ART GENERATOR",
                  font=("Arial", 14, "bold")).pack(pady=10)

        # Project management
        project_frame = ttk.LabelFrame(self.control_frame, text="Project")
        project_frame.pack(fill=tk.X, pady=5)
        ttk.Button(project_frame, text="New Project", command=self.new_project).pack(side=tk.LEFT, padx=2, fill=tk.X,
                                                                                     expand=True)
        ttk.Button(project_frame, text="Save Project", command=self.save_project).pack(side=tk.LEFT, padx=2, fill=tk.X,
                                                                                       expand=True)
        ttk.Button(project_frame, text="Load Project", command=self.load_project).pack(side=tk.LEFT, padx=2, fill=tk.X,
                                                                                       expand=True)

        # Image selection
        img_frame = ttk.Frame(self.control_frame)
        img_frame.pack(fill=tk.X, pady=5)
        ttk.Button(img_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=(0, 5))
        self.img_path_label = ttk.Label(img_frame, text="No image selected", wraplength=200)
        self.img_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Dice size controls
        ttk.Label(self.control_frame, text="Dice Grid Width:").pack(anchor="w", pady=(15, 0))
        self.width_slider = ttk.Scale(
            self.control_frame,
            from_=10,
            to=150,
            variable=self.dice_width,
            command=self.update_size_label
        )
        self.width_slider.pack(fill=tk.X, pady=5)
        self.size_label = ttk.Label(self.control_frame, text="Grid Size: 30 x ?")
        self.size_label.pack(anchor="w")

        # Image adjustments
        adj_frame = ttk.LabelFrame(self.control_frame, text="Image Adjustments")
        adj_frame.pack(fill=tk.X, pady=10)

        ttk.Label(adj_frame, text="Brightness:").pack(anchor="w", padx=5)
        ttk.Scale(
            adj_frame,
            from_=0.5,
            to=2.0,
            variable=self.brightness,
            command=self.preview_adjustments
        ).pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(adj_frame, text="Contrast:").pack(anchor="w", padx=5, pady=(5, 0))
        ttk.Scale(
            adj_frame,
            from_=0.5,
            to=2.0,
            variable=self.contrast,
            command=self.preview_adjustments
        ).pack(fill=tk.X, padx=5, pady=2)

        # Dice settings
        dice_frame = ttk.LabelFrame(self.control_frame, text="Dice Settings")
        dice_frame.pack(fill=tk.X, pady=5)

        ttk.Label(dice_frame, text="Dice Color:").pack(anchor="w", padx=5)
        color_combo = ttk.Combobox(
            dice_frame,
            textvariable=self.dice_color,
            state="readonly",
            width=10
        )
        color_combo['values'] = tuple(self.dice_colors.keys())
        color_combo.pack(fill=tk.X, padx=5, pady=2)
        color_combo.bind("<<ComboboxSelected>>", self.update_dice_preview)

        ttk.Label(dice_frame, text="Preview Dice Size:").pack(anchor="w", padx=5, pady=(5, 0))
        dice_size_slider = ttk.Scale(
            dice_frame,
            from_=5,
            to=50,
            variable=self.dice_size,
            command=self.update_dice_size
        )
        dice_size_slider.pack(fill=tk.X, padx=5, pady=2)
        self.dice_size_label = ttk.Label(dice_frame, text=f"Dice Size: {self.dice_size.get()}px")
        self.dice_size_label.pack(anchor="w", padx=5)

        # Dice preview
        ttk.Label(self.control_frame, text="Dice Preview:").pack(anchor="w", pady=(15, 0))
        self.dice_preview_frame = ttk.Frame(self.control_frame, height=120, width=120, relief="solid")
        self.dice_preview_frame.pack(pady=10)
        self.dice_preview_frame.pack_propagate(False)

        self.dice_preview_canvas = tk.Canvas(self.dice_preview_frame, bg="#34495e", highlightthickness=0)
        self.dice_preview_canvas.pack(fill=tk.BOTH, expand=True)

        # Dice count
        self.dice_count_label = ttk.Label(self.control_frame, text="Total Dice: 0", font=("Arial", 12))
        self.dice_count_label.pack(pady=10)

        # Action buttons
        action_frame = ttk.Frame(self.control_frame)
        action_frame.pack(fill=tk.X, pady=5)
        ttk.Button(
            action_frame,
            text="Generate Dice Art",
            command=self.generate_dice_art,
            style="TButton"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(
            action_frame,
            text="Export Dice Grid",
            command=self.export_dice_grid
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Advanced export
        adv_frame = ttk.LabelFrame(self.control_frame, text="Advanced Export")
        adv_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            adv_frame,
            text="Export as Image",
            command=self.export_image
        ).pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(
            adv_frame,
            text="Generate Dice List",
            command=self.generate_dice_list
        ).pack(fill=tk.X, padx=5, pady=2)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Preview area
        preview_top = ttk.Frame(self.preview_frame)
        preview_top.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(preview_top, text="Original Image", font=("Arial", 12)).pack(side=tk.LEFT)
        ttk.Label(preview_top, text="Dice Art Preview", font=("Arial", 12)).pack(side=tk.RIGHT)

        preview_mid = ttk.Frame(self.preview_frame)
        preview_mid.pack(fill=tk.BOTH, expand=True)

        # Original image frame
        self.orig_img_frame = ttk.Frame(preview_mid, height=self.preview_size, width=self.preview_size)
        self.orig_img_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.orig_img_frame.pack_propagate(False)

        self.orig_img_canvas = tk.Canvas(self.orig_img_frame, bg="#34495e", highlightthickness=0)
        self.orig_img_canvas.pack(fill=tk.BOTH, expand=True)
        self.orig_img_label = ttk.Label(self.orig_img_canvas, text="No image loaded", background="#34495e",
                                        foreground="#bdc3c7")
        self.orig_img_label.place(relx=0.5, rely=0.5, anchor="center")

        # Dice art preview frame
        self.dice_img_frame = ttk.Frame(preview_mid, height=self.preview_size, width=self.preview_size)
        self.dice_img_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.dice_img_frame.pack_propagate(False)

        self.dice_img_canvas = tk.Canvas(self.dice_img_frame, bg="#34495e", highlightthickness=0)
        self.dice_img_canvas.pack(fill=tk.BOTH, expand=True)
        self.dice_img_label = ttk.Label(self.dice_img_canvas, text="Generate dice art to see preview",
                                        background="#34495e", foreground="#bdc3c7")
        self.dice_img_label.place(relx=0.5, rely=0.5, anchor="center")

        # Draw initial dice preview
        self.draw_dice_preview(3)

    def set_status(self, message):
        self.status_var.set(message)
        self.root.update_idletasks()

    def new_project(self):
        self.image_path = ""
        self.dice_grid = None
        self.total_dice = 0
        self.img_path_label.config(text="No image selected")
        self.orig_img_canvas.delete("all")
        self.dice_img_canvas.delete("all")
        self.orig_img_label.place(relx=0.5, rely=0.5, anchor="center")
        self.dice_img_label.place(relx=0.5, rely=0.5, anchor="center")
        self.dice_count_label.config(text="Total Dice: 0")
        self.set_status("New project created")
        self.current_project = None

    def save_project(self):
        if not self.image_path or not self.dice_grid:
            messagebox.showwarning("No Data", "No dice art to save")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".diceproj",
            filetypes=[("Dice Art Project", "*.diceproj"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                project_data = {
                    "image_path": self.image_path,
                    "dice_width": self.dice_width.get(),
                    "dice_color": self.dice_color.get(),
                    "brightness": self.brightness.get(),
                    "contrast": self.contrast.get(),
                    "dice_grid": self.dice_grid,
                    "total_dice": self.total_dice
                }

                with open(file_path, "w") as f:
                    json.dump(project_data, f)

                self.current_project = file_path
                self.set_status(f"Project saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {str(e)}")

    def load_project(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Dice Art Project", "*.diceproj"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r") as f:
                    project_data = json.load(f)

                self.image_path = project_data["image_path"]
                self.dice_width.set(project_data["dice_width"])
                self.dice_color.set(project_data["dice_color"])
                self.brightness.set(project_data["brightness"])
                self.contrast.set(project_data["contrast"])
                self.dice_grid = project_data["dice_grid"]
                self.total_dice = project_data["total_dice"]

                # Update UI
                self.img_path_label.config(text=os.path.basename(self.image_path))
                self.display_image(self.image_path)
                self.update_size_label()
                self.dice_count_label.config(text=f"Total Dice: {self.total_dice}")
                self.create_dice_art_preview()
                self.draw_dice_preview(self.dice_grid[0][0])
                self.current_project = file_path
                self.set_status(f"Project loaded: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project: {str(e)}")

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if file_path:
            self.image_path = file_path
            self.img_path_label.config(text=os.path.basename(file_path))
            self.display_image(file_path)
            self.update_size_label()
            self.set_status(f"Loaded image: {os.path.basename(file_path)}")

    def display_image(self, path):
        try:
            img = Image.open(path)

            # Apply adjustments
            img = self.apply_adjustments(img)

            img.thumbnail((self.preview_size, self.preview_size))
            self.tk_img = ImageTk.PhotoImage(img)

            # Clear canvas and display image
            self.orig_img_canvas.delete("all")
            self.orig_img_canvas.create_image(
                self.preview_size / 2,
                self.preview_size / 2,
                image=self.tk_img,
                anchor="center"
            )
            self.orig_img_label.place_forget()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")

    def apply_adjustments(self, img):
        """Apply brightness and contrast adjustments to image"""
        # Convert to RGB for adjustments
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Apply brightness
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(self.brightness.get())

        # Apply contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(self.contrast.get())

        return img

    def preview_adjustments(self, *args):
        if self.image_path:
            self.display_image(self.image_path)

    def update_size_label(self, *args):
        if not self.image_path:
            self.size_label.config(text="Grid Size: 30 x ?")
            return

        try:
            with Image.open(self.image_path) as img:
                width = self.dice_width.get()
                aspect_ratio = img.height / img.width
                height = max(1, round(width * aspect_ratio))
                self.size_label.config(text=f"Grid Size: {width} x {height}")
        except:
            self.size_label.config(text="Grid Size: 30 x ?")

    def update_dice_size(self, *args):
        self.dice_size_label.config(text=f"Dice Size: {int(self.dice_size.get())}px")
        if self.dice_grid:
            self.create_dice_art_preview()

    def update_dice_preview(self, *args):
        if self.dice_grid:
            self.draw_dice_preview(self.dice_grid[0][0] if self.dice_grid else 3)
            self.create_dice_art_preview()

    def draw_dice_preview(self, value):
        self.dice_preview_canvas.delete("all")

        # Dice face representations
        dice_faces = {
            1: [(0.5, 0.5)],
            2: [(0.3, 0.3), (0.7, 0.7)],
            3: [(0.3, 0.3), (0.5, 0.5), (0.7, 0.7)],
            4: [(0.3, 0.3), (0.3, 0.7), (0.7, 0.3), (0.7, 0.7)],
            5: [(0.3, 0.3), (0.3, 0.7), (0.5, 0.5), (0.7, 0.3), (0.7, 0.7)],
            6: [(0.3, 0.3), (0.3, 0.5), (0.3, 0.7), (0.7, 0.3), (0.7, 0.5), (0.7, 0.7)]
        }

        # Draw dice
        size = 100
        padding = 10
        bg_color, dot_color = self.dice_colors.get(self.dice_color.get(), ("#e0e0e0", "#2c3e50"))

        self.dice_preview_canvas.create_rectangle(
            padding, padding, size + padding, size + padding,
            fill=bg_color, outline="#34495e", width=2
        )

        # Draw dots
        dot_radius = 8
        for x, y in dice_faces[value]:
            self.dice_preview_canvas.create_oval(
                (x * size) + padding - dot_radius,
                (y * size) + padding - dot_radius,
                (x * size) + padding + dot_radius,
                (y * size) + padding + dot_radius,
                fill=dot_color, outline=""
            )

    def generate_dice_art(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Please load an image first")
            return

        try:
            self.set_status("Generating dice art...")
            # Open and process image
            img = Image.open(self.image_path)
            width = self.dice_width.get()
            aspect_ratio = img.height / img.width
            height = max(1, round(width * aspect_ratio))
            self.total_dice = width * height
            self.dice_count_label.config(text=f"Total Dice: {self.total_dice}")

            # Apply adjustments
            img = self.apply_adjustments(img)

            # Convert to grayscale and resize
            img = img.convert('L')
            img = img.resize((width, height))

            # Create dice grid
            self.dice_grid = []
            for y in range(height):
                row = []
                for x in range(width):
                    brightness = img.getpixel((x, y))
                    # Map brightness to dice value (1=lightest, 6=darkest)
                    dice_value = 6 - int(brightness / 42.5)  # 255/6 ≈ 42.5
                    dice_value = max(1, min(6, dice_value))
                    row.append(dice_value)
                self.dice_grid.append(row)

            # Create dice art preview
            self.create_dice_art_preview()

            # Update dice preview
            self.draw_dice_preview(self.dice_grid[0][0])

            self.set_status(f"Dice art generated! Total dice: {self.total_dice}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate dice art: {str(e)}")
            self.set_status("Error generating dice art")

    def create_dice_art_preview(self):
        if not self.dice_grid:
            return

        # Create a new image for the dice art preview
        dice_size = int(self.dice_size.get())  # Size of each die in preview
        height = len(self.dice_grid)
        width = len(self.dice_grid[0])

        # Create a blank image
        preview_img = Image.new("RGB", (width * dice_size, height * dice_size), "#34495e")

        # Draw each dice
        for y in range(height):
            for x in range(width):
                dice_value = self.dice_grid[y][x]
                self.draw_dice_on_image(preview_img, x * dice_size, y * dice_size, dice_size, dice_value)

        # Resize for display
        preview_img.thumbnail((self.preview_size, self.preview_size))
        self.dice_tk_img = ImageTk.PhotoImage(preview_img)

        # Display on canvas
        self.dice_img_canvas.delete("all")
        self.dice_img_canvas.create_image(
            self.preview_size / 2,
            self.preview_size / 2,
            image=self.dice_tk_img,
            anchor="center"
        )
        self.dice_img_label.place_forget()

    def draw_dice_on_image(self, img, x, y, size, value):
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)

        # Dice colors
        bg_color, dot_color = self.dice_colors.get(self.dice_color.get(), ("#e0e0e0", "#2c3e50"))
        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
        dot_rgb = tuple(int(dot_color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))

        # Draw dice background
        draw.rectangle([x, y, x + size - 1, y + size - 1], fill=bg_rgb, outline="#95a5a6")

        # Dice face representations
        dice_faces = {
            1: [(0.5, 0.5)],
            2: [(0.3, 0.3), (0.7, 0.7)],
            3: [(0.3, 0.3), (0.5, 0.5), (0.7, 0.7)],
            4: [(0.3, 0.3), (0.3, 0.7), (0.7, 0.3), (0.7, 0.7)],
            5: [(0.3, 0.3), (0.3, 0.7), (0.5, 0.5), (0.7, 0.3), (0.7, 0.7)],
            6: [(0.3, 0.3), (0.3, 0.5), (0.3, 0.7), (0.7, 0.3), (0.7, 0.5), (0.7, 0.7)]
        }

        # Draw dots
        dot_radius = size * 0.15
        for pos in dice_faces[value]:
            px = x + (pos[0] * size)
            py = y + (pos[1] * size)
            draw.ellipse(
                [px - dot_radius, py - dot_radius,
                 px + dot_radius, py + dot_radius],
                fill=dot_rgb
            )

    def export_dice_grid(self):
        if not self.dice_grid:
            messagebox.showwarning("No Data", "Generate dice art first")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    for row in self.dice_grid:
                        f.write(" ".join(map(str, row)) + "\n")
                messagebox.showinfo("Success", f"Dice grid saved to:\n{file_path}")
                self.set_status(f"Dice grid exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")

    def export_image(self):
        if not self.dice_grid:
            messagebox.showwarning("No Data", "Generate dice art first")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Files", "*.png"), ("JPEG Files", "*.jpg"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                self.set_status("Exporting image...")
                dice_size = 20  # Use a fixed size for full export
                height = len(self.dice_grid)
                width = len(self.dice_grid[0])

                # Create a blank image
                export_img = Image.new("RGB", (width * dice_size, height * dice_size), "white")

                # Draw each dice
                for y in range(height):
                    for x in range(width):
                        dice_value = self.dice_grid[y][x]
                        self.draw_dice_on_image(export_img, x * dice_size, y * dice_size, dice_size, dice_value)

                export_img.save(file_path)
                messagebox.showinfo("Success", f"Dice art image saved to:\n{file_path}")
                self.set_status(f"Image exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {str(e)}")

    def generate_dice_list(self):
        if not self.dice_grid:
            messagebox.showwarning("No Data", "Generate dice art first")
            return

        # Count dice values
        counts = {i: 0 for i in range(1, 7)}
        for row in self.dice_grid:
            for value in row:
                counts[value] += 1

        # Create dice list text
        dice_list = "Dice Requirements:\n"
        dice_list += "------------------\n"
        for value, count in counts.items():
            dice_list += f"Dice {value}: {count}\n"

        dice_list += "------------------\n"
        dice_list += f"Total Dice: {self.total_dice}\n"

        # Show in a new window
        list_window = tk.Toplevel(self.root)
        list_window.title("Dice Requirements")
        list_window.geometry("300x250")

        text_area = tk.Text(list_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, dice_list)
        text_area.config(state=tk.DISABLED)

        # Add save button
        save_btn = ttk.Button(list_window, text="Save List",
                              command=lambda: self.save_dice_list(dice_list))
        save_btn.pack(pady=5)

    def save_dice_list(self, dice_list):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(dice_list)
                messagebox.showinfo("Success", f"Dice list saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedDiceArtGenerator(root)
    root.mainloop()