import cv2
import numpy as np

class MedicalImagePreprocessor:
    def __init__(self, target_size=(224, 224)):
        self.target_size = target_size

    def preprocess(self, image_bytes):
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Invalid or corrupted medical image payload.")
            
        # Convert to grayscale for medical image analysis
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Gaussian Blur for noise suppression
        denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        # Resize to standard model dimension
        resized = cv2.resize(denoised, self.target_size, interpolation=cv2.INTER_AREA)
        
        # Normalize pixel intensities [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        return normalized, img.shape
