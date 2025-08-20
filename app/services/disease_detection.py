"""
Coffee Disease Detection Service

This service provides AI-powered coffee disease detection using a trained PyTorch ResNext50 model.
Detects 5 categories: Healthy, Miner, Rust, Phoma, Cercospora
"""
import torch
import torch.nn as nn
from torchvision import transforms
import numpy as np
import timm
from PIL import Image
import cv2
import os
import logging
from typing import Optional, Tuple, List, Dict, Any
import tempfile
import io

logger = logging.getLogger(__name__)

class DiseaseDetectionConfig:
    """Configuration for disease detection model"""
    MODEL_NAME = 'resnext50_32x4d'
    IMAGE_SIZE = 128
    TARGET_CLASSES = 5
    CATEGORY_MAPPING = {
        0: 'Healthy', 
        1: 'Miner', 
        2: 'Rust', 
        3: 'Phoma', 
        4: 'Cercospora'
    }

class CustomResNext(nn.Module):
    """Custom ResNext model for coffee disease classification"""
    
    def __init__(self, model_name: str = 'resnext50_32x4d', pretrained: bool = False):
        super().__init__()
        self.model = timm.create_model(model_name, pretrained=pretrained)
        n_features = self.model.fc.in_features
        self.model.fc = nn.Linear(n_features, DiseaseDetectionConfig.TARGET_CLASSES)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

class DiseaseDetectionService:
    """Service for coffee disease detection using trained PyTorch model"""
    
    def __init__(self):
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.transforms = self._get_inference_transforms()
        self._load_model()
    
    def _get_inference_transforms(self) -> transforms.Compose:
        """Get image preprocessing transforms"""
        return transforms.Compose([
            transforms.Resize((DiseaseDetectionConfig.IMAGE_SIZE, DiseaseDetectionConfig.IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])
    
    def _load_model(self) -> None:
        """Load the trained PyTorch model"""
        try:
            # Look for model file in different possible locations
            model_paths = [
                '/Users/pompompurin/Desktop/Guka/guka-ai-agent/models/resnext50_32x4d_fold1_best.pth',
                '/Users/pompompurin/Desktop/Guka/gukas-backend/apps/detection/trained_model/resnext50_32x4d_fold1_best.pth',
                '/Users/pompompurin/Desktop/Guka/guka-ai-agent/Coffee_Disease_Detection/trained_model/resnext50_32x4d_fold1_best.pth'
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                logger.error("Disease detection model file not found in any expected location")
                return
            
            self.model = CustomResNext(
                model_name=DiseaseDetectionConfig.MODEL_NAME, 
                pretrained=False
            )
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.eval()
            self.model.to(self.device)
            logger.info(f"Disease detection model loaded successfully from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load disease detection model: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if the disease detection service is available"""
        return self.model is not None
    
    def preprocess_image(self, image_data: Any) -> Optional[torch.Tensor]:
        """Preprocess image data for model inference"""
        try:
            # Handle different input types
            if isinstance(image_data, str):
                # File path
                image = cv2.imread(image_data)
                if image is None:
                    logger.error(f"Could not load image from path: {image_data}")
                    return None
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
            elif isinstance(image_data, bytes):
                # Bytes data from file upload
                image = Image.open(io.BytesIO(image_data))
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
            elif isinstance(image_data, np.ndarray):
                # NumPy array
                image = cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB)
                
            elif isinstance(image_data, Image.Image):
                # PIL Image
                image = cv2.cvtColor(np.array(image_data), cv2.COLOR_RGB2BGR)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
            else:
                logger.error(f"Unsupported image input type: {type(image_data)}")
                return None
            
            # Convert to PIL and apply transforms
            pil_image = Image.fromarray(image)
            input_tensor = self.transforms(pil_image).unsqueeze(0).to(self.device)
            
            return input_tensor
            
        except Exception as e:
            logger.error(f"Image preprocessing error: {e}")
            return None
    
    def predict_disease(self, image_data: Any) -> Dict[str, Any]:
        """
        Predict coffee disease from image
        
        Args:
            image_data: Image data (file path, bytes, numpy array, or PIL Image)
            
        Returns:
            Dictionary with prediction results
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Disease detection service not available',
                'predicted_class': None,
                'confidence': 0.0,
                'probabilities': {},
                'recommendations': []
            }
        
        try:
            # Preprocess image
            input_tensor = self.preprocess_image(image_data)
            if input_tensor is None:
                return {
                    'success': False,
                    'error': 'Failed to preprocess image',
                    'predicted_class': None,
                    'confidence': 0.0,
                    'probabilities': {},
                    'recommendations': []
                }
            
            # Model inference
            with torch.no_grad():
                output = self.model(input_tensor)
                probabilities = torch.softmax(output, dim=1)
                predicted_class_index = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_class_index].item()
            
            # Get predicted class name
            predicted_class = DiseaseDetectionConfig.CATEGORY_MAPPING.get(
                predicted_class_index, 'Unknown'
            )
            
            # Create probability dictionary
            prob_dict = {}
            for idx, class_name in DiseaseDetectionConfig.CATEGORY_MAPPING.items():
                prob_dict[class_name] = float(probabilities[0][idx].item())
            
            # Generate recommendations
            recommendations = self._get_recommendations(predicted_class, confidence)
            
            logger.info(f"Disease prediction: {predicted_class} (confidence: {confidence:.4f})")
            
            return {
                'success': True,
                'error': None,
                'predicted_class': predicted_class,
                'confidence': float(confidence),
                'probabilities': prob_dict,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Disease prediction error: {e}")
            return {
                'success': False,
                'error': f'Prediction failed: {str(e)}',
                'predicted_class': None,
                'confidence': 0.0,
                'probabilities': {},
                'recommendations': []
            }
    
    def _get_recommendations(self, predicted_class: str, confidence: float) -> List[str]:
        """Generate recommendations based on prediction"""
        recommendations = []
        
        if confidence < 0.6:
            recommendations.append(
                "Low confidence prediction. Consider taking multiple photos from different angles for better accuracy."
            )
        
        if predicted_class == "Healthy":
            recommendations.extend([
                "Your coffee plants appear healthy! Continue with regular care and monitoring.",
                "Maintain good agricultural practices including proper spacing, pruning, and fertilization.",
                "Monitor regularly for early signs of disease to catch issues before they spread."
            ])
        
        elif predicted_class == "Miner":
            recommendations.extend([
                "Coffee Leaf Miner detected. This pest creates tunnels in coffee leaves.",
                "Apply appropriate insecticides like chlorpyrifos or imidacloprid.",
                "Improve farm sanitation by removing fallen leaves and pruning affected branches.",
                "Consider biological control using parasitic wasps if available in your area."
            ])
        
        elif predicted_class == "Rust":
            recommendations.extend([
                "Coffee Leaf Rust detected. This is a serious fungal disease that can cause significant yield losses.",
                "Apply copper-based fungicides immediately.",
                "Improve air circulation by proper pruning and spacing of plants.",
                "Remove and destroy infected leaves to prevent spread.",
                "Consider resistant coffee varieties for future planting."
            ])
        
        elif predicted_class == "Phoma":
            recommendations.extend([
                "Phoma disease detected. This fungal infection affects coffee leaves and can spread quickly.",
                "Apply systemic fungicides containing propiconazole or tebuconazole.",
                "Ensure proper drainage to reduce moisture levels around plants.",
                "Remove infected plant material and dispose of it away from the farm.",
                "Monitor closely and treat early to prevent spread."
            ])
        
        elif predicted_class == "Cercospora":
            recommendations.extend([
                "Cercospora leaf spot detected. This fungal disease causes brown spots on leaves.",
                "Apply fungicides containing mancozeb or copper compounds.",
                "Improve air circulation through proper pruning.",
                "Avoid overhead irrigation to reduce leaf wetness.",
                "Remove fallen leaves and infected plant material."
            ])
        
        return recommendations
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status"""
        return {
            'service_name': 'Disease Detection',
            'status': 'healthy' if self.is_available() else 'unhealthy',
            'model_loaded': self.is_available(),
            'device': str(self.device),
            'supported_classes': list(DiseaseDetectionConfig.CATEGORY_MAPPING.values())
        }

# Global service instance
disease_detection_service = DiseaseDetectionService()
