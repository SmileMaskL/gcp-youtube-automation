from setuptools import setup, find_packages

setup(
    name="youtube_automation",
    version="1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "google-generativeai>=0.3.0",
        "opencv-python-headless>=4.5.0",
        "Pillow>=9.0.0",
        "python-dotenv>=0.19.0",
        "moviepy>=1.0.3",
        "google-cloud-texttospeech>=2.0.0"  # 음성 합성용 추가
    ],
)
