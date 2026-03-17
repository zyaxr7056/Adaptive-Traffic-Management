class TrafficLogic:
    def __init__(self):
        # Phases: 
        # 0 = NS Green, 1 = NS Yellow, 2 = All Red (Clearance)
        # 3 = EW Green, 4 = EW Yellow, 5 = All Red (Clearance)
        self.phase = 0 
        self.timer = 0
        
        # Timing constraints (assuming the simulation runs at 60 FPS)
        self.min_green = 60 * 3    # Minimum 3 seconds
        self.max_green = 60 * 10   # Maximum 10 seconds
        self.yellow_time = 60 * 2  # 2 seconds for yellow
        self.clearance_time = 60 * 2 # 2 seconds of ALL RED to clear the intersection
        
    def update_lights(self, counts):
        self.timer += 1
        
        ns_demand = counts['N'] + counts['S']
        ew_demand = counts['E'] + counts['W']
        
        # Phase 0: North/South Green
        if self.phase == 0:
            time_up = self.timer >= self.max_green
            empty_but_waiting = (self.timer >= self.min_green) and (ns_demand == 0 and ew_demand > 0)
            
            if time_up or empty_but_waiting:
                self.phase = 1 
                self.timer = 0
                
        # Phase 1: North/South Yellow
        elif self.phase == 1:
            if self.timer >= self.yellow_time:
                self.phase = 2 # Go to Clearance Phase
                self.timer = 0
                
        # Phase 2: ALL RED (Clearing North/South traffic)
        elif self.phase == 2:
            if self.timer >= self.clearance_time:
                self.phase = 3 # Proceed to East/West Green
                self.timer = 0
                
        # Phase 3: East/West Green
        elif self.phase == 3:
            time_up = self.timer >= self.max_green
            empty_but_waiting = (self.timer >= self.min_green) and (ew_demand == 0 and ns_demand > 0)
            
            if time_up or empty_but_waiting:
                self.phase = 4 
                self.timer = 0
                
        # Phase 4: East/West Yellow
        elif self.phase == 4:
            if self.timer >= self.yellow_time:
                self.phase = 5 # Go to Clearance Phase
                self.timer = 0
                
        # Phase 5: ALL RED (Clearing East/West traffic)
        elif self.phase == 5:
            if self.timer >= self.clearance_time:
                self.phase = 0 # Loop back to North/South Green
                self.timer = 0
                
        # Return the corresponding light states for the current phase (0=Red, 1=Green, 2=Yellow)
        if self.phase == 0:
            return {'N': 1, 'S': 1, 'E': 0, 'W': 0}
        elif self.phase == 1:
            return {'N': 2, 'S': 2, 'E': 0, 'W': 0}
        elif self.phase == 2:
            return {'N': 0, 'S': 0, 'E': 0, 'W': 0} # All Red
        elif self.phase == 3:
            return {'N': 0, 'S': 0, 'E': 1, 'W': 1}
        elif self.phase == 4:
            return {'N': 0, 'S': 0, 'E': 2, 'W': 2}
        elif self.phase == 5:
            return {'N': 0, 'S': 0, 'E': 0, 'W': 0} # All Red

