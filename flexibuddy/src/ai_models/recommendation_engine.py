import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd
import os
import json
import time
from datetime import datetime

class RecommendationEngine:
    """
    AI-powered recommendation engine for FlexiBuddy.
    Uses machine learning to analyze user behavior and recommend appropriate activities.
    """
    def __init__(self, data_logger=None):
        self.data_logger = data_logger
        self.user_profile = {
            "attention_spans": [],
            "frustration_events": [],
            "activity_preferences": {},
            "engagement_scores": {}
        }
        self.model = None
        self.scaler = StandardScaler()
        
        # Minimum data points needed for ML-based recommendations
        self.min_data_points = 5
        
        # Load existing profile if available
        self._load_profile()
    
    def _load_profile(self, profile_path=None):
        """
        Loads user profile from file if available
        """
        if not profile_path and self.data_logger:
            # Use data logger's base directory
            base_dir = getattr(self.data_logger, 'base_dir', None)
            if base_dir:
                profile_path = os.path.join(base_dir, 'user_profile.json')
        
        if profile_path and os.path.exists(profile_path):
            try:
                with open(profile_path, 'r') as f:
                    self.user_profile = json.load(f)
                print(f"Loaded user profile from {profile_path}")
            except Exception as e:
                print(f"Error loading user profile: {e}")
    
    def save_profile(self, profile_path=None):
        """
        Saves user profile to file
        """
        if not profile_path and self.data_logger:
            # Use data logger's base directory
            base_dir = getattr(self.data_logger, 'base_dir', None)
            if base_dir:
                profile_path = os.path.join(base_dir, 'user_profile.json')
        
        if profile_path:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(profile_path), exist_ok=True)
                with open(profile_path, 'w') as f:
                    json.dump(self.user_profile, f, indent=2)
                print(f"Saved user profile to {profile_path}")
            except Exception as e:
                print(f"Error saving user profile: {e}")
    
    def update_profile(self, activity_data=None, attention_data=None, frustration_data=None):
        """
        Updates user profile with new data
        
        Args:
            activity_data (DataFrame): Activity completion data
            attention_data (DataFrame): Attention span data
            frustration_data (DataFrame): Frustration events data
        """
        if activity_data is not None and not activity_data.empty:
            # Update activity preferences
            for _, row in activity_data.iterrows():
                activity = row['activity']
                success = float(row['success']) if isinstance(row['success'], str) else row['success']
                duration = float(row['duration']) if isinstance(row['duration'], str) else row['duration']
                
                if activity not in self.user_profile['activity_preferences']:
                    self.user_profile['activity_preferences'][activity] = []
                
                self.user_profile['activity_preferences'][activity].append({
                    'timestamp': row.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    'duration': duration,
                    'success': success
                })
        
        if attention_data is not None and not attention_data.empty:
            # Update attention spans
            for _, row in attention_data.iterrows():
                self.user_profile['attention_spans'].append({
                    'timestamp': row.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    'activity': row['activity'],
                    'duration': float(row['attention_duration']) if isinstance(row['attention_duration'], str) else row['attention_duration']
                })
        
        if frustration_data is not None and not frustration_data.empty:
            # Update frustration events
            for _, row in frustration_data.iterrows():
                self.user_profile['frustration_events'].append({
                    'timestamp': row.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    'activity': row['activity'],
                    'level': int(row['frustration_level']) if isinstance(row['frustration_level'], str) else row['frustration_level']
                })
        
        # Calculate engagement scores
        self._calculate_engagement_scores()
        
        # Train model if enough data
        if self._has_sufficient_data():
            self._train_model()
    
    def _calculate_engagement_scores(self):
        """
        Calculates engagement scores for each activity based on attention spans and success rates
        """
        # Reset engagement scores
        self.user_profile['engagement_scores'] = {}
        
        # Get all unique activities
        activities = set()
        for activity_list in self.user_profile['activity_preferences'].values():
            for item in activity_list:
                activities.add(item.get('activity', ''))
        
        for attention_span in self.user_profile['attention_spans']:
            activities.add(attention_span.get('activity', ''))
        
        # Calculate scores for each activity
        for activity in activities:
            if not activity:  # Skip empty activity names
                continue
                
            # Get attention spans for this activity
            activity_attention = [span['duration'] for span in self.user_profile['attention_spans'] 
                                if span.get('activity') == activity]
            
            # Get success rates for this activity
            activity_success = [item['success'] for items in self.user_profile['activity_preferences'].values() 
                              for item in items if item.get('activity') == activity]
            
            # Get frustration events for this activity
            activity_frustration = [event['level'] for event in self.user_profile['frustration_events'] 
                                   if event.get('activity') == activity]
            
            # Calculate engagement score
            avg_attention = np.mean(activity_attention) if activity_attention else 0
            avg_success = np.mean(activity_success) if activity_success else 0
            avg_frustration = np.mean(activity_frustration) if activity_frustration else 0
            
            # Engagement formula: higher attention and success is good, higher frustration is bad
            engagement_score = (avg_attention * 0.4) + (avg_success * 0.4) - (avg_frustration * 0.2)
            
            # Store the score
            self.user_profile['engagement_scores'][activity] = max(0, engagement_score)  # Ensure non-negative
    
    def _has_sufficient_data(self):
        """
        Checks if there's enough data to train a model
        """
        return len(self.user_profile['attention_spans']) >= self.min_data_points
    
    def _train_model(self):
        """
        Trains a machine learning model on user data
        """
        try:
            # Prepare features
            features = []
            for activity in self.user_profile['engagement_scores'].keys():
                # Get attention spans for this activity
                activity_attention = [span['duration'] for span in self.user_profile['attention_spans'] 
                                    if span.get('activity') == activity]
                
                # Get frustration events for this activity
                activity_frustration = [event['level'] for event in self.user_profile['frustration_events'] 
                                       if event.get('activity') == activity]
                
                # Calculate features
                avg_attention = np.mean(activity_attention) if activity_attention else 0
                avg_frustration = np.mean(activity_frustration) if activity_frustration else 0
                engagement_score = self.user_profile['engagement_scores'].get(activity, 0)
                
                features.append([avg_attention, avg_frustration, engagement_score])
            
            if features:
                # Scale features
                X = self.scaler.fit_transform(features)
                
                # Train KMeans model to cluster activities
                n_clusters = min(3, len(features))  # At most 3 clusters, but not more than we have activities
                self.model = KMeans(n_clusters=n_clusters, random_state=42)
                self.model.fit(X)
                print(f"Trained recommendation model with {len(features)} activities")
            else:
                print("No features available for training")
        except Exception as e:
            print(f"Error training model: {e}")
            self.model = None
    
    def get_recommended_activity(self, current_activity=None, reason="timeout", frustration_level=0):
        """
        Gets a recommended activity based on user profile and current state
        
        Args:
            current_activity (str): Currently running activity
            reason (str): Reason for change ('timeout', 'boredom', 'voice_command')
            frustration_level (int): User's frustration level (0-10)
            
        Returns:
            str: Recommended activity name
        """
        # If we don't have enough data or model isn't trained, return None
        if not self._has_sufficient_data() or self.model is None:
            return None
        
        try:
            # Get all activities
            activities = list(self.user_profile['engagement_scores'].keys())
            
            # Filter out current activity
            available_activities = [a for a in activities if a != current_activity]
            if not available_activities:
                return None
            
            # Prepare input features for prediction
            # For high frustration, we want calming activities
            if frustration_level > 7:
                # Look for activities with low frustration events
                activity_frustration = {}
                for activity in available_activities:
                    events = [event['level'] for event in self.user_profile['frustration_events'] 
                             if event.get('activity') == activity]
                    activity_frustration[activity] = np.mean(events) if events else 0
                
                # Sort by lowest frustration
                sorted_activities = sorted(activity_frustration.items(), key=lambda x: x[1])
                if sorted_activities:
                    return sorted_activities[0][0]  # Return activity with lowest frustration
            
            # For boredom, we want engaging activities
            if reason == "boredom":
                # Sort by highest engagement score
                sorted_activities = sorted([(a, self.user_profile['engagement_scores'].get(a, 0)) 
                                          for a in available_activities], key=lambda x: x[1], reverse=True)
                if sorted_activities:
                    return sorted_activities[0][0]  # Return activity with highest engagement
            
            # Use model for normal recommendations
            # Prepare features for each available activity
            features = []
            for activity in available_activities:
                # Get attention spans for this activity
                activity_attention = [span['duration'] for span in self.user_profile['attention_spans'] 
                                    if span.get('activity') == activity]
                
                # Get frustration events for this activity
                activity_frustration = [event['level'] for event in self.user_profile['frustration_events'] 
                                       if event.get('activity') == activity]
                
                # Calculate features
                avg_attention = np.mean(activity_attention) if activity_attention else 0
                avg_frustration = np.mean(activity_frustration) if activity_frustration else 0
                engagement_score = self.user_profile['engagement_scores'].get(activity, 0)
                
                features.append([avg_attention, avg_frustration, engagement_score])
            
            # Scale features
            X = self.scaler.transform(features)
            
            # Get cluster assignments
            clusters = self.model.predict(X)
            
            # Find the best cluster (highest average engagement)
            cluster_scores = {}
            for i, cluster in enumerate(clusters):
                if cluster not in cluster_scores:
                    cluster_scores[cluster] = []
                cluster_scores[cluster].append(self.user_profile['engagement_scores'].get(available_activities[i], 0))
            
            best_cluster = max(cluster_scores.items(), key=lambda x: np.mean(x[1]) if x[1] else 0)[0]
            
            # Get activities in the best cluster
            best_activities = [available_activities[i] for i, cluster in enumerate(clusters) if cluster == best_cluster]
            
            if best_activities:
                # Return the activity with highest engagement in the best cluster
                return max(best_activities, key=lambda a: self.user_profile['engagement_scores'].get(a, 0))
        
        except Exception as e:
            print(f"Error getting recommendation: {e}")
        
        return None
    
    def get_insights(self):
        """
        Generates AI insights about the user's learning patterns
        
        Returns:
            dict: Dictionary of insights
        """
        insights = {
            "preferred_activities": [],
            "attention_pattern": "",
            "frustration_triggers": [],
            "recommendations": []
        }
        
        # Only generate insights if we have enough data
        if not self._has_sufficient_data():
            return insights
        
        try:
            # Get preferred activities
            if self.user_profile['engagement_scores']:
                sorted_activities = sorted(self.user_profile['engagement_scores'].items(), 
                                          key=lambda x: x[1], reverse=True)
                insights["preferred_activities"] = [a[0] for a in sorted_activities[:3]]
            
            # Analyze attention pattern
            if self.user_profile['attention_spans']:
                attention_durations = [span['duration'] for span in self.user_profile['attention_spans']]
                avg_attention = np.mean(attention_durations) if attention_durations else 0
                
                if avg_attention < 60:  # Less than 1 minute
                    insights["attention_pattern"] = "Very short attention span. Recommend frequent activity changes."
                elif avg_attention < 120:  # 1-2 minutes
                    insights["attention_pattern"] = "Short attention span. Recommend engaging activities with quick rewards."
                elif avg_attention < 240:  # 2-4 minutes
                    insights["attention_pattern"] = "Moderate attention span. Balance between focus and variety."
                else:  # 4+ minutes
                    insights["attention_pattern"] = "Good attention span. Can handle longer, more complex activities."
            
            # Identify frustration triggers
            if self.user_profile['frustration_events']:
                # Group by activity
                activity_frustration = {}
                for event in self.user_profile['frustration_events']:
                    activity = event.get('activity', '')
                    if activity:
                        if activity not in activity_frustration:
                            activity_frustration[activity] = []
                        activity_frustration[activity].append(event['level'])
                
                # Find activities with highest average frustration
                avg_frustration = {a: np.mean(levels) for a, levels in activity_frustration.items()}
                sorted_frustration = sorted(avg_frustration.items(), key=lambda x: x[1], reverse=True)
                
                insights["frustration_triggers"] = [a[0] for a in sorted_frustration[:2]]
            
            # Generate recommendations
            if insights["preferred_activities"] and insights["frustration_triggers"]:
                # Recommend activities similar to preferred ones but not in frustration triggers
                recommendations = [a for a in insights["preferred_activities"] 
                                 if a not in insights["frustration_triggers"]]
                
                if recommendations:
                    insights["recommendations"] = recommendations
                else:
                    # If all preferred activities are frustration triggers,
                    # recommend activities not in either list
                    other_activities = [a for a in self.user_profile['engagement_scores'].keys() 
                                      if a not in insights["preferred_activities"] 
                                      and a not in insights["frustration_triggers"]]
                    insights["recommendations"] = other_activities[:2]
        
        except Exception as e:
            print(f"Error generating insights: {e}")
        
        return insights