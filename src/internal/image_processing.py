# -*- coding: utf-8 -*-
import cv2 as cv
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Optional, Tuple
from pillow_heif import register_heif_opener  #type: ignore
from kangen.config import MIN_CONTOUR_AREA, APPROX_POLY_EPSILON

register_heif_opener()

def convert_heic_to_jpeg(heic_path: Path) -> Path:
    """Converts HEIC images to JPEG and returns the new path."""
    if heic_path.suffix.lower() not in ['.heic', '.heif']:
        return heic_path
        
    jpeg_path = heic_path.with_suffix('.jpg')
    # Skip if already exists to save time during dev/testing
    if jpeg_path.exists():
        return jpeg_path

    try:
        with Image.open(heic_path) as image:
            image.convert("RGB").save(jpeg_path, "JPEG")
        return jpeg_path
    except Exception as e:
        raise ValueError(f"Failed to convert HEIC to JPEG: {e}")

def load_image(path: Path) -> np.ndarray:
    """Loads an image from path using OpenCV."""
    img = cv.imread(str(path))
    if img is None:
        raise ValueError(f"Could not read image from {path}")
    return img

def _order_points(pts: np.ndarray) -> np.ndarray:
    """Sorts the 4 points of a contour into: TL, TR, BR, BL."""
    pts = pts.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # Top-left: smallest sum
    rect[2] = pts[np.argmax(s)] # Bottom-right: largest sum
    
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # Top-right: smallest diff
    rect[3] = pts[np.argmax(diff)] # Bottom-left: largest diff
    
    return rect

def _create_content_blobs(image: np.ndarray) -> np.ndarray:
    """Creates a binary 'blob' image to find the main table contour."""
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    inverted_gray = cv.bitwise_not(gray)
    _ , binary = cv.threshold(inverted_gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    # Using a rectangular kernel to connect horizontal text lines
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (10, 3))
    dilated = cv.dilate(binary, kernel, iterations=3)
    return dilated

def find_table_contour(image: np.ndarray) -> Optional[np.ndarray]:
    """Finds the largest rectangular contour, assumed to be the table."""
    blob_image = _create_content_blobs(image)
    contours, _ = cv.findContours(blob_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
        
    # Sort by area, largest first
    contours = sorted(contours, key=cv.contourArea, reverse=True)
    
    for contour in contours:
        if cv.contourArea(contour) < MIN_CONTOUR_AREA:
            continue
            
        peri = cv.arcLength(contour, True)
        approx = cv.approxPolyDP(contour, APPROX_POLY_EPSILON * peri, True)
        
        # If we found a quadrilateral
        if len(approx) == 4:
            return approx
            
    return None

def warp_perspective(image: np.ndarray, contour: np.ndarray) -> np.ndarray:
    """Applies a perspective transform to get a top-down view of the table."""
    ordered_contour = _order_points(contour)
    (tl, tr, br, bl) = ordered_contour
    
    # Calculate new width and height
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    new_width = max(int(widthA), int(widthB))
    
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    new_height = max(int(heightA), int(heightB))
    
    destination_points = np.array([
        [0, 0], 
        [new_width - 1, 0], 
        [new_width - 1, new_height - 1], 
        [0, new_height - 1]
    ], dtype="float32")
    
    matrix = cv.getPerspectiveTransform(ordered_contour, destination_points)
    warped_image = cv.warpPerspective(image, matrix, (new_width, new_height))
    
    return warped_image

def save_debug_image(image: np.ndarray, path: Path, contour: Optional[np.ndarray] = None):
    """Saves debug visualization of image with optional contour overlay."""
    try:
        if contour is not None:
            debug_img = image.copy()
            cv.drawContours(debug_img, [contour], -1, (0, 255, 0), 3)
            cv.imwrite(str(path), debug_img)
        else:
            cv.imwrite(str(path), image)
    except Exception as e:
        print(f"Warning: Could not save debug image to {path}: {e}")