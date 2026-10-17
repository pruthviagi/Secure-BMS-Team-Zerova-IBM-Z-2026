%% SecureBMS: Single EV, Single Battery, Single Cell
% Exactly 1000 data points
% Synthetic simulation for hackathon demonstration
% Team Zerova | IBM Z Datathon 2026
% Output: SecureBMS_OneBattery_OneCell_1000.csv

clear;
clc;
close all;
rng(42);

%% 1. Simulation settings
N = 1000;
dt = 1;                     % Sampling interval (seconds)

timestamp = (1:N)';
vehicle_id = ones(N,1);
battery_id = ones(N,1);
cell_id = ones(N,1);

%% 2. Vehicle movement
speed_kmph = max(0, ...
    30 + 10*sin(timestamp/80) + 4*randn(N,1));

km_travelled = cumsum(speed_kmph * dt / 3600);

%% 3. Road hump events
hump_event = zeros(N,1);

% Simulate 12 hump encounters
hump_positions = sort(randperm(N,12));
hump_event(hump_positions) = 1;

humps_encountered = cumsum(hump_event);

%% 4. Battery current
current_A = max(0.1, ...
    3 + 2*sin(timestamp/35) + 0.8*randn(N,1));

%% 5. Vibration caused by road conditions
vibration_g = abs(0.04 + 0.025*randn(N,1));

hump_idx = find(hump_event == 1);
vibration_g(hump_idx) = 1.2 + 1.6*rand(length(hump_idx),1);

%% 6. Simulated microcrack progression
microcrack_index = zeros(N,1);
crack = 0.02;

for i = 1:N
    if hump_event(i) == 1
        crack = crack + 0.015 + 0.01*rand;
    end
      microcrack_index(i) = min(crack,1);
end

%% 7. Internal resistance (milliohms)
internal_resistance_mohm = ...
    28 + 35*microcrack_index ...
    + 0.002*timestamp + 0.5*randn(N,1);

internal_resistance_mohm = ...
    max(5,internal_resistance_mohm);

%% 8. State of charge (SoC)
soc_pct = max(5, ...
    90 - cumsum(current_A)*100/(3600*5));

%% 9. Cell voltage
OCV = 3.0 + 1.2*soc_pct/100;

voltage_V = OCV ...
    - current_A.*internal_resistance_mohm/1000 ...
    + 0.008*randn(N,1);

%% 10. Cell temperature
temperature_C = 28 ...
    + 0.015*current_A.^2 ...
    + 0.8*microcrack_index ...
    + 0.15*randn(N,1);

%% 11. State of health (SoH)
soh_pct = max(60, ...
    100 - 4*microcrack_index - 0.0002*timestamp);

%% 12. Simulated anomaly label
anomaly_label = double( ...
    internal_resistance_mohm > 42 | ...
    temperature_C > 42 | ...
    (microcrack_index > 0.30 & voltage_V < 3.45));

%% 13. Create the dataset
data = table( ...
    timestamp, vehicle_id, battery_id, cell_id, ...
    speed_kmph, km_travelled, hump_event, ...
    humps_encountered, current_A, voltage_V, ...
    temperature_C, soc_pct, soh_pct, ...
    internal_resistance_mohm, vibration_g, ...
    microcrack_index, anomaly_label);

%% 14. Export CSV file
filename = 'SecureBMS_OneBattery_OneCell_1000.csv';
writetable(data,filename);

%% 15. Display results
fprintf('\nSecureBMS simulation completed!\n');
fprintf('Number of batteries: 1\n');
fprintf('Number of cells: 1\n');
fprintf('Number of data points: %d\n',height(data));
fprintf('Distance travelled: %.3f km\n',km_travelled(end));
fprintf('Total humps encountered: %d\n',humps_encountered(end));
fprintf('Anomaly records: %d\n',sum(anomaly_label));
fprintf('CSV saved as: %s\n',filename);

disp(data(1:10,:));

%% 16. Plot battery telemetry
figure('Color','w','Name','SecureBMS One Cell');

subplot(5,1,1);
plot(timestamp,km_travelled,'b');
ylabel('Distance (km)');
title('Single EV Battery Cell Simulation');
grid on;

subplot(5,1,2);
stairs(timestamp,humps_encountered,'m');
ylabel('Hump count');
grid on;

subplot(5,1,3);
plot(timestamp,internal_resistance_mohm,'r');
ylabel('Resistance (mOhm)');
grid on;

subplot(5,1,4);
plot(timestamp,temperature_C,'Color',[0.85 0.4 0.1]);
ylabel('Temp (C)');
grid on;

subplot(5,1,5);
plot(timestamp,microcrack_index,'k');
ylabel('Crack index');
xlabel('Time (seconds)');
grid on;

%% 17. Verify output size
assert(height(data) == 1000);
assert(width(data) == 17);

disp('Verification successful: 1000 rows and 17 columns.');
