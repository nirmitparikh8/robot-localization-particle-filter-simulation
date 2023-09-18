import numpy as np
import cv2

# Load Map
map = cv2.imread("map.png", 0)
HEIGHT, WIDTH = map.shape

# Robot Position Initially
rx, ry, rtheta = (WIDTH / 4, HEIGHT / 4, 0)

# Constants
STEP = 5
TURN = np.radians(25)
SIGMA_STEP = 0.5
SIGMA_TURN = np.radians(5)
NUM_PARTICLES = 3000
SIGMA_SENSOR = 2
SIGMA_POS = 2

# Function to get user input
def get_user_input():
    fwd = 0
    turn = 0
    halt = False
    k = cv2.waitKey(0)
    
    if k == ord('w'):  # Forward Key
        fwd = STEP
    elif k == ord('d'):  # Right Key
        turn = TURN
    elif k == ord('a'):  # Left Key
        turn = -TURN
    elif k == ord('s'):  # Backward Key
        fwd = -STEP
    else:
        halt = True
    
    return fwd, turn, halt

# Function to simulate robot motion
def simulate_robot_motion(rx, ry, rtheta, fwd, turn):
    fwd_noisy = np.random.normal(fwd, SIGMA_STEP, 1)
    rx += fwd_noisy * np.cos(rtheta)
    ry += fwd_noisy * np.sin(rtheta)
    
    turn_noisy = np.random.normal(turn, SIGMA_TURN, 1)
    rtheta += turn_noisy
    
    return rx, ry, rtheta

# Initialize particles
def initialize_particles():
    particles = np.random.rand(NUM_PARTICLES, 3)
    particles *= np.array((WIDTH, HEIGHT, np.radians(360)))
    return particles

# Move particles
def move_particles(particles, fwd, turn):
    particles[:, 0] += fwd * np.cos(particles[:, 2])
    particles[:, 1] += fwd * np.sin(particles[:, 2])
    particles[:, 2] += turn
    
    particles[:, 0] = np.clip(particles[:, 0], 0.0, WIDTH - 1)
    particles[:, 1] = np.clip(particles[:, 1], 0.0, HEIGHT - 1)
    
    return particles

# Simulate sensor measurement
def simulate_sensor_measurement(x, y, noisy=False):
    x = int(x)
    y = int(y)
    
    if noisy:
        return np.random.normal(map[y, x], SIGMA_SENSOR, 1)
    
    return map[y, x]

# Compute particle weights
def compute_particle_weights(particles, robot_sensor):    
    errors = np.zeros(NUM_PARTICLES)
    
    for i in range(NUM_PARTICLES):
        elevation = simulate_sensor_measurement(particles[i, 0], particles[i, 1], noisy=False)
        errors[i] = abs(robot_sensor - elevation)
    
    weights = np.max(errors) - errors
    
    weights[
        (particles[:, 0] == 0) | (particles[:, 0] == WIDTH - 1) | 
        (particles[:, 1] == 0) | (particles[:, 1] == HEIGHT - 1)
    ] = 0.0
    
    weights = weights ** 3
    
    return weights

# Resample particles
def resample_particles(particles, weights):
    probability = weights / np.sum(weights)
    new_index = np.random.choice(
        NUM_PARTICLES, size=NUM_PARTICLES, p=probability)
    particles = particles[new_index, :]
    return particles

# Add noise to particles
def add_noise_to_particles(particles):
    noise = np.concatenate((
        np.random.normal(0, SIGMA_POS, (NUM_PARTICLES, 1)),
        np.random.normal(0, SIGMA_POS, (NUM_PARTICLES, 1)),
        np.random.normal(0, SIGMA_TURN, (NUM_PARTICLES, 1)),
    ), axis=1)
    
    particles += noise
    
    return particles

# Display the map, robot, and particles
def display_map(rx, ry, particles):
    lmap = cv2.cvtColor(map, cv2.COLOR_GRAY2BGR)
    
    # Display particles
    if len(particles) > 0:
        for i in range(NUM_PARTICLES):
            cv2.circle(
                lmap, 
                (int(particles[i, 0]), int(particles[i, 1])), 
                1, 
                (255, 0, 0), 
                1)
    
    # Display robot
    cv2.circle(lmap, (int(rx), int(ry)), 5, (0, 255, 0), 10)

    # Display best guess
    if len(particles) > 0:
        px = np.mean(particles[:, 0])
        py = np.mean(particles[:, 1])
        cv2.circle(lmap, (int(px), int(py)), 5, (0, 0, 255), 5)
        print("Estimated Robot Position (Best Guess):")
        print(f"X: {px}")
        print(f"Y: {py}")


    cv2.imshow('map', lmap)

# Main loop
particles = initialize_particles()
while True:
    display_map(rx, ry, particles)
    fwd, turn, halt = get_user_input()
    
    if halt:
        break
    
    rx, ry, rtheta = simulate_robot_motion(rx, ry, rtheta, fwd, turn)
    particles = move_particles(particles, fwd, turn)
    
    if fwd != 0:
        robot_sensor = simulate_sensor_measurement(rx, ry, noisy=True)        
        weights = compute_particle_weights(particles, robot_sensor)
        particles = resample_particles(particles, weights)
        particles = add_noise_to_particles(particles)

cv2.destroyAllWindows()
