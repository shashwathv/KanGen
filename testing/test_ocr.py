import cv2 as cv
import easyocr

path = '/home/guts/Projects/anki_flashcards/images.png'

def processing(img_path):
    try:
        img = cv.imread(str(img_path))
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (5,5), 0)
        thresh = cv.adaptiveThreshold(blur, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 2)
        return thresh
    except FileNotFoundError as e:
        print(f"Error: {e}")

def recog(img):
    try:
        reader = easyocr.Reader(['en', 'ja'], gpu=False)
        text = reader.readtext(img, detail=0, paragraph=True)
        return text
    except FileNotFoundError as e:
        print(f"Error: {e}")

def main():
    img_path = path
    try:
        p_img = processing(path)
        img_text = recog(p_img)
        print(img_text)

    except FileExistsError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()