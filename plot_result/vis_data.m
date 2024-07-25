% Filenames of the JSON files
filenames = {'cost_no_reduction.json','cost_oppo.json', 'cost_opti.json'};

% Preallocate a structure to hold the data
data = struct();

% Loop through each file and read the content
for i = 1:length(filenames)
    % Check if the file exists
    if isfile(filenames{i})
        % Open the file
        fid = fopen(filenames{i}, 'r');
        
        % Read the file's content
        raw = fread(fid, inf, 'char=>char')';
        fclose(fid);
        
        % Decode the JSON data
        data.(erase(filenames{i}, '.json')) = jsondecode(raw);
    else
        error('File %s does not exist.', filenames{i});
    end
end

% Assume data.cost_oppo and data.cost_opti are structures with identical fields
truck_ids = fieldnames(data.cost_oppo);  % Get the list of truck IDs
percentage_differences = zeros(length(truck_ids), 1);  % Preallocate array

% Loop through each truck to calculate the percentage difference
for i = 1:length(truck_ids)
    truck_id = truck_ids{i};
    oppo = data.cost_oppo.(truck_id);
    opti = data.cost_opti.(truck_id);
    
    % Calculate the percentage difference
    if oppo ~= 0  % Avoid division by zero
        percentage_differences(i) = ((oppo - opti) / oppo) * 100;
    else
        percentage_differences(i) = 0;  % If oppo is 0, handle appropriately
    end
end

% Remove all zero percentage differences for the second histogram
filtered_differences = percentage_differences(percentage_differences ~= 0);

% Plot histograms as subplots
% figure;
% subplot(1, 2, 1);  % First subplot
% histogram(percentage_differences, 50);  % 50 bins for the histogram
% title('Histogram of All Cost Reduction Percentages');
% xlabel('Percentage Reduction (%)');  % Updated xlabel
% ylabel('Frequency of Trucks');
% grid on;
% 
% subplot(1, 2, 2);  % Second subplot
% histogram(filtered_differences, 50);  % Using the same number of bins
% title('Histogram with 0% Differences Removed');
% xlabel('Percentage Reduction (%)');  % Updated xlabel
% ylabel('Frequency of Trucks');
% grid on;


% Set the path to the CSV file
filepath = 'start_configuration.csv';
% Read the CSV file. Assume first row is headers.
opts = detectImportOptions(filepath);
opts.DataLines = [2, Inf];  % Assuming the first line is headers
configData = readtable(filepath, opts);
% Create a table with unique carrier IDs
carrier_ids = unique(configData.CarrierIndex);
carrier_costs_oppo = zeros(length(carrier_ids), 1);
carrier_costs_opti = zeros(length(carrier_ids), 1);
carrier_costs_nr   = zeros(length(carrier_ids), 1);
% Prepare a table for results
costs_by_carrier = table(carrier_ids, carrier_costs_oppo, carrier_costs_opti, ...
                         'VariableNames', {'CarrierID', 'TotalCostOppo', 'TotalCostOpti'});
% Loop through all trucks based on truck_ids array
for i = 0:length(truck_ids)-1
    truck_id = i;  % Use fieldnames directly to ensure correct ID format
    % Find the index in configData that matches this truck_id
    idx = find(configData.TruckIndex==truck_id);
    if ~isempty(idx)  % Check if any matching index is found
        carrier_id = configData.CarrierIndex(idx);  % Get carrier ID from found inde
        % Aggregate costs into the table
        table_idx = find(costs_by_carrier.CarrierID == carrier_id);
        carrier_costs_oppo(table_idx,1) = carrier_costs_oppo(table_idx,1) + data.cost_oppo.(truck_ids{i+1});
        carrier_costs_opti(table_idx,1) = carrier_costs_opti(table_idx,1) + data.cost_opti.(truck_ids{i+1});
        carrier_costs_nr(table_idx,1)   = carrier_costs_nr(table_idx,1) + data.cost_no_reduction.(truck_ids{i+1});
    else
        % Handle cases where no matching truck_id is found in configData
        warning('Truck ID %s not found in configData', truck_id);
    end
end

% Assuming truck_ids are correct and identical across all data sets
truck_ids = fieldnames(data.cost_no_reduction);  % Assuming all JSON data contain the same trucks

% Initialize arrays for percentage reductions
percentage_reduction_oppo = zeros(length(carrier_ids), 1);
percentage_reduction_opti = zeros(length(carrier_ids), 1);

% Loop through each truck ID to calculate reductions
for i = 1:length(carrier_ids)
    truck_id = truck_ids{i};
    cost_no_red = carrier_costs_nr(i);
    cost_oppo = carrier_costs_oppo(i);
    cost_opti = carrier_costs_opti(i);
    
    % Check to avoid division by zero
    if cost_no_red ~= 0
        percentage_reduction_oppo(i) = ((cost_no_red - cost_oppo) / cost_no_red) * 100;
        percentage_reduction_opti(i) = ((cost_no_red - cost_opti) / cost_no_red) * 100;
    else
        percentage_reduction_oppo(i) = NaN; % Handle cases where no reduction cost is zero
        percentage_reduction_opti(i) = NaN;
    end
end
% Create figure for plotting histograms
% Calculate global minimum and maximum for consistent bin edges
all_data = [percentage_reduction_oppo; percentage_reduction_opti];
min_val = min(all_data);
max_val = max(all_data);

% Create bin edges that cover the entire range of data
bin_edges = linspace(min_val, max_val, 50);  % 50 bins
figure;

% Subplot 1: Histogram for No Reduction to Oppo
subplot(2, 1, 1);  % 2 rows, 1 column, first plot
histogram(percentage_reduction_oppo, 'BinEdges', bin_edges, 'FaceColor', 'blue');
title('Cost Reduction by opportunstic platooning');
xlabel('Percentage Cost Reduction');
ylabel('Frequency of Carriers');
grid on;
ylim([0, 200]);  % Set y-axis limits from 0 to 200
% Subplot 2: Histogram for No Reduction to Opti
subplot(2, 1, 2);  % 2 rows, 1 column, second plot
histogram(percentage_reduction_opti, 'BinEdges', bin_edges, 'FaceColor', 'red');
title('Cost Reduction by privacy-preserving cross-carrier platooning');
xlabel('Percentage Cost Reduction');
ylabel('Frequency of Carriers');
grid on;
ylim([0, 200]);  % Set y-axis limits from 0 to 200
% Ensure subplots have the same x-axis limits for direct comparison
% Ensure subplots have the same x-axis and y-axis limits for direct comparison
linkaxes(findall(gcf, 'Type', 'axes'), 'xy');
