# comment_filter.py - AI Comment Filtering System

import re
import nltk
from textblob import TextBlob
# from profanity_check import predict as is_profane
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle
import os

def check_profanity(self, text):
    text_lower = text.lower()
    profane = any(word in text_lower for word in self.bad_words)
    return bool(profane)

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class CommentFilter:
    """
    AI-powered comment filtering system that analyzes comments for:
    1. Sentiment analysis (positive/negative)
    2. Toxicity detection
    3. Profanity filtering
    4. Spam detection
    5. Inappropriate content detection
    """
    
    def __init__(self):
        self.bad_words = [
            'hate', 'stupid', 'idiot', 'dumb', 'ugly', 'loser', 'kill', 'die', 
            'trash', 'garbage', 'worthless', 'pathetic', 'disgusting', 'gross',
            'annoying', 'boring', 'lame', 'sucks', 'awful', 'terrible'
        ]
        
        self.positive_indicators = [
            'love', 'awesome', 'amazing', 'beautiful', 'great', 'fantastic', 
            'wonderful', 'excellent', 'perfect', 'nice', 'good', 'cool', 
            'sweet', 'adorable', 'cute', 'inspiring', 'motivating', 'happy',
            'joyful', 'brilliant', 'outstanding', 'marvelous', 'superb'
        ]
        
        self.humor_indicators = [
            'haha', 'lol', 'lmao', 'funny', 'hilarious', 'joke', 'laugh', 
            'comedy', 'humor', 'witty', 'clever', 'amusing', 'entertaining',
            '😂', '😄', '😆', '🤣', '😊', '😋', 'rofl', 'giggle'
        ]
        
        self.load_or_train_model()
    
    def load_or_train_model(self):
        """Load existing model or create a simple one"""
        try:
            # Try to load existing model
            self.vectorizer = joblib.load('comment_vectorizer.pkl')
            self.classifier = joblib.load('comment_classifier.pkl')
        except:
            # Create simple model if none exists
            self.create_simple_model()
    
    def create_simple_model(self):
        """Create a simple rule-based + ML model"""
        # Sample training data (in real app, you'd have much more)
        training_texts = [
            # Good comments
            "This is amazing!", "Love this post", "So beautiful", "Great work",
            "Awesome content", "This made me smile", "So inspiring", "Perfect",
            "Haha this is funny", "LOL great joke", "You're so talented",
            
            # Bad comments
            "This is stupid", "You're an idiot", "This sucks", "Hate this",
            "You're ugly", "This is trash", "Kill yourself", "Die loser",
            "Disgusting content", "This is garbage", "You're pathetic"
        ]
        
        training_labels = [1] * 11 + [0] * 11  # 1 = good, 0 = bad
        
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        X = self.vectorizer.fit_transform(training_texts)
        
        self.classifier = LogisticRegression()
        self.classifier.fit(X, training_labels)
        
        # Save the model
        joblib.dump(self.vectorizer, 'comment_vectorizer.pkl')
        joblib.dump(self.classifier, 'comment_classifier.pkl')
    
    def analyze_sentiment(self, text):
        """Analyze sentiment using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': subjectivity
            }
        except:
            return {'sentiment': 'neutral', 'polarity': 0, 'subjectivity': 0}
    
    def check_profanity(self, text):
        """Check for profanity and inappropriate language"""
        try:
            # Use profanity-check library
            is_profane_result = is_profane(text)
            return is_profane_result
        except:
            # Fallback to manual checking
            text_lower = text.lower()
            return any(bad_word in text_lower for bad_word in self.bad_words)
    
    def check_toxicity(self, text):
        """Check for toxic content using ML model"""
        try:
            text_vector = self.vectorizer.transform([text])
            prediction = self.classifier.predict_proba(text_vector)[0]
            
            # prediction[1] is probability of being good
            # prediction[0] is probability of being bad
            toxicity_score = prediction[0]  # Higher means more toxic
            
            return {
                'is_toxic': toxicity_score > 0.6,
                'toxicity_score': toxicity_score,
                'confidence': max(prediction)
            }
        except:
            return {'is_toxic': False, 'toxicity_score': 0, 'confidence': 0.5}
    
    def check_spam(self, text):
        """Simple spam detection"""
        text_lower = text.lower()
        spam_indicators = [
            'click here', 'buy now', 'free money', 'winner', 'congratulations',
            'www.', 'http', '.com', 'discount', 'offer', 'deal', 'cash',
            'urgent', 'limited time', 'act now', 'call now'
        ]
        
        # Check for excessive repetition
        words = text_lower.split()
        if len(words) > 0:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            max_freq = max(word_freq.values())
            if max_freq > len(words) * 0.5:  # More than 50% repetition
                return True
        
        # Check for spam indicators
        spam_count = sum(1 for indicator in spam_indicators if indicator in text_lower)
        return spam_count >= 2
    
    def detect_humor(self, text):
        """Detect humorous content"""
        text_lower = text.lower()
        humor_score = 0
        
        # Check for humor indicators
        for indicator in self.humor_indicators:
            if indicator in text_lower:
                humor_score += 1
        
        # Check for question marks (often used in jokes)
        humor_score += text.count('?') * 0.5
        
        # Check for exclamation marks (enthusiasm)
        humor_score += min(text.count('!'), 3) * 0.3
        
        return humor_score > 0.5
    
    def analyze_comment(self, comment_text):
        """
        Comprehensive comment analysis
        Returns detailed analysis and recommendation
        """
        if not comment_text or len(comment_text.strip()) == 0:
            return {
                'should_display': False,
                'reason': 'Empty comment',
                'analysis': {}
            }
        
        # Run all analyses
        sentiment_analysis = self.analyze_sentiment(comment_text)
        is_profane = self.check_profanity(comment_text)
        toxicity_analysis = self.check_toxicity(comment_text)
        is_spam = self.check_spam(comment_text)
        is_humorous = self.detect_humor(comment_text)
        
        # Decision logic
        should_display = True
        reasons = []
        
        # Filter out bad content
        if is_profane:
            should_display = False
            reasons.append('Contains profanity')
        
        if toxicity_analysis['is_toxic']:
            should_display = False
            reasons.append(f'Toxic content (confidence: {toxicity_analysis["confidence"]:.2f})')
        
        if is_spam:
            should_display = False
            reasons.append('Detected as spam')
        
        if sentiment_analysis['polarity'] < -0.5:
            should_display = False
            reasons.append('Very negative sentiment')
        
        # Boost good content
        if is_humorous:
            reasons.append('Contains humor')
        
        if sentiment_analysis['sentiment'] == 'positive':
            reasons.append('Positive sentiment')
        
        return {
            'should_display': should_display,
            'reasons': reasons,
            'analysis': {
                'sentiment': sentiment_analysis,
                'is_profane': is_profane,
                'toxicity': toxicity_analysis,
                'is_spam': is_spam,
                'is_humorous': is_humorous,
                'text_length': len(comment_text),
                'word_count': len(comment_text.split())
            }
        }
    
    def filter_comments(self, comments_list):
        """
        Filter a list of comments and return only appropriate ones
        """
        filtered_comments = []
        
        for comment in comments_list:
            analysis = self.analyze_comment(comment.get('content', ''))
            
            if analysis['should_display']:
                # Add analysis data to comment
                comment['ai_analysis'] = analysis['analysis']
                comment['ai_reasons'] = analysis['reasons']
                filtered_comments.append(comment)
        
        return filtered_comments

# Initialize the filter (create global instance)
comment_filter = CommentFilter()

def analyze_comment_text(text):
    """Helper function to analyze single comment"""
    return comment_filter.analyze_comment(text)

def filter_comment_list(comments):
    """Helper function to filter comment list"""
    return comment_filter.filter_comments(comments)