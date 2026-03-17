class TrafficLogic:
    def __init__(self):
        self.roads = ['N', 'E', 'S', 'W']
        self.current_road_idx = 0
        
        self.state = 'GREEN'
        self.timer = 0
        
        # Base timing (at 60 FPS)
        self.min_green = 60 * 3      # Minimum 3 seconds so cars can physically start moving
        self.absolute_max = 60 * 15  # Hard cap at 15 seconds so no road starves forever
        self.yellow_time = 60 * 3
        self.clearance_time = 60 * 2
        
    def update_lights(self, counts):
        self.timer += 1
        active_road = self.roads[self.current_road_idx]
        
        if self.state == 'GREEN':
            # 1. ADAPTIVE DURATION: Calculate time needed (approx 2 seconds per waiting car)
            # It will never be less than min_green, and never more than absolute_max
            time_needed_frames = counts[active_road] * (60 * 2)
            dynamic_max_green = min(self.absolute_max, max(self.min_green, time_needed_frames))
            
            time_up = self.timer >= dynamic_max_green
            empty_but_waiting = (self.timer >= self.min_green) and (counts[active_road] == 0)
            
            if time_up or empty_but_waiting:
                self.state = 'YELLOW'
                self.timer = 0
                
        elif self.state == 'YELLOW':
            if self.timer >= self.yellow_time:
                self.state = 'ALL_RED'
                self.timer = 0
                
        elif self.state == 'ALL_RED':
            if self.timer >= self.clearance_time:
                self.state = 'GREEN'
                self.timer = 0
                
                # 2. ADAPTIVE ROUTING: Who gets the green light next?
                # Look at the other 3 roads (exclude the one that just went)
                other_roads = [r for r in self.roads if r != active_road]
                
                # Find the road with the biggest traffic jam
                best_next_road = max(other_roads, key=lambda r: counts.get(r, 0))
                
                # If that road actually has cars waiting, give it the green light!
                if counts[best_next_road] > 0:
                    self.current_road_idx = self.roads.index(best_next_road)
                else:
                    # If the whole intersection is empty, just rest and cycle normally
                    self.current_road_idx = (self.current_road_idx + 1) % len(self.roads)
        
        # --- RETURN LIGHT STATES ---
        lights = {'N': 0, 'S': 0, 'E': 0, 'W': 0}
        
        if self.state == 'GREEN':
            lights[active_road] = 1
        elif self.state == 'YELLOW':
            lights[active_road] = 2
            
        return lights
