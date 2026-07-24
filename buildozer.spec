[app]

# (str) Title of your application
title = Secret Vault

# (str) Package name
package.name = secretvault

# (str) Package domain (reverse-DNS style)
package.domain = com.nathaniel

# (str) Source code where main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,kv,png,jpg,jpeg,gif,webp,mp4,mov,mkv,3gp,ttf,json

# (str) Application versioning
version = 1.0

# (list) Application requirements
# ffpyplayer and ffmpeg have been REMOVED to prevent build crashes.
# Kivy will natively play .mp4 files using Android's default media player.
requirements = python3,kivy==2.3.0,plyer,pillow

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# ==========================================
# ANDROID SPECIFIC SETTINGS
# ==========================================

# (int) Target Android API, minimum API and NDK/SDK
android.api = 34
android.minapi = 21

# (list) Permissions required for Plyer's FileChooser to grab media
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO

# (list) Supported architectures (Modern 64-bit and standard 32-bit)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Disable Android's automatic cloud/adb backup of app data.
# Prevents Google Drive from backing up the hidden media folder.
android.allow_backup = False

# (bool) Enforce private storage for the app
android.private_storage = True

# (bool) Enable AndroidX support (Crucial for Plyer compatibility on API 34)
android.enable_androidx = True

# (str) Presplash background color (Matches your kv background)
android.presplash_color = #000000

# (str) Format of the release artifact (apk for direct installation)
android.release_artifact = apk

[buildozer]

# (int) Log level (2 = debug, best for catching build errors)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
