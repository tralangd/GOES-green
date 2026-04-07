% Generate Images and Videos for README.md


%% Read Data

file_ID = fopen('../data/BIN/batch_merged.bin','r');
data1 = reshape(fread(file_ID,'*uint32'),[256,256,256,256]) ;               % BGRV bin counts
data2 = reshape(uint32(sum(data1,2)),[256,256,256]) ;                       % BRV bin counts
data3 = log10(double(data2)) ;                                              % log scale for clarity
fclose(file_ID);

file_ID = fopen('../data/LUT_base.bin','r');
LUT_base = reshape(fread(file_ID,'*uint8'),[256,256,256]) ;
fclose(file_ID);

file_ID = fopen('../data/LUT.bin','r');
LUT = reshape(fread(file_ID,'*uint8'),[256,256,256]) ;
fclose(file_ID);


%% Total BRV Triplet Counts

MIN = 0 ;
MAX = max(max(max(data3))) ;

% custom color map 0-255 to 'green' -> 'yellow' -> 'red'
cmap = [ 
         linspace(0,1,128) , ones([1,128]) ; 
         ones([1,128]) , linspace(1,0,128) ; 
         zeros([1,256])
       ]' ;

v = VideoWriter("green_heatmap.mp4", "MPEG-4");
v.FrameRate = 30;
v.Quality = 100;
open(v)

fig = figure(1);
hold on
xlim([0,255])
xlabel('Red')
ylim([0,255])
ylabel('Blue')
clim([MIN,MAX])
colormap(fig,cmap)
c = colorbar ;
c.Label.String = 'log_{10} bin count';

for V = 1:256
    imagesc(data3(:,:,V));
    title(['Veggie = ', num2str(V-1)])
    writeVideo(v,getframe(fig));
end

close(v)


%% Green Channl Distribution of specific BRV triplets (Large Bin Counts)

% points to plot
B = [25 50 75 100 125 150 175];
R = [25 50 75 100 125 150 175];
V = [30 55 80 105 130 155 180];

figure(2);
hold on

if size(B) ~= size(R) | size(R) ~= size(V)
    error('BRV vectors must be the same size')
end

legend_names = cell(length(B),1);
for ii = 1:length(B)
    plot(0:255,data1(B(ii),:,R(ii),V(ii)));
    legend_names{ii} = ['(B,R,V) = (' num2str(B(ii)) ',' num2str(R(ii)) ',' num2str(V(ii)) ')'];
end

xlim([0,255])
xlabel('Green Intensity')
ylim([0,250000]) % adjust as needed
ylabel('Bin Count')
legend(legend_names)
title('Green Intensity Distibution')


%% Green Channl Distribution of specific BRV triplets (Smaller Bin Counts)

% points to plot
B = [75 100 125 150 175 200 225];
R = [75 100 125 150 175 200 225];
V = [77 102 127 152 177 203 228];

figure(3);
hold on

if size(B) ~= size(R) | size(R) ~= size(V)
    error('BRV vectors must be the same size')
end

legend_names = cell(length(B),1);
for ii = 1:length(B)
    plot(0:255,data1(B(ii),:,R(ii),V(ii)));
    legend_names{ii} = ['(B,R,V) = (' num2str(B(ii)) ',' num2str(R(ii)) ',' num2str(V(ii)) ')'];
end

xlim([0,255])
xlabel('Green Intensity')
ylim([0,15000]) % adjust as needed
ylabel('Bin Count')
legend(legend_names)
title('Green Intensity Distibution')


%% Green Channl Distribution of specific BRV triplets (Even Smaller Bin Counts)

% points to plot
B = [75 100 125 150 175 200 225];
R = [75 100 125 150 175 200 225];
V = [75 100 125 150 175 200 225];

figure(4);
hold on

if size(B) ~= size(R) | size(R) ~= size(V)
    error('BRV vectors must be the same size')
end

legend_names = cell(length(B),1);
for ii = 1:length(B)
    plot(0:255,data1(B(ii),:,R(ii),V(ii)));
    legend_names{ii} = ['(B,R,V) = (' num2str(B(ii)) ',' num2str(R(ii)) ',' num2str(V(ii)) ')'];
end

xlim([0,255])
xlabel('Green Intensity')
ylim([0,1000]) % adjust as needed
ylabel('Bin Count')
legend(legend_names)
title('Green Intensity Distibution')

%% LUT Before and After Interpolation

v = VideoWriter("LUT_slices.mp4", "MPEG-4");
v.FrameRate = 30;
v.Quality = 100;
open(v)

fig = figure(5);

for V = 1:256

    R = repmat(0:255,[256,1]);
    G = double(LUT_base(:,:,V));
    B = transpose(repmat(0:255,[256,1]));
    
    img = uint8(zeros([256,256,3]));
    img(:,:,1) = uint8(R .* double(G > 0)) + uint8(255 * double(G==0)) ;
    img(:,:,2) = uint8(G .* double(G > 0)) + uint8(255 * double(G==0)) ;
    img(:,:,3) = uint8(B .* double(G > 0)) + uint8(255 * double(G==0)) ;
    
    subplot(1,2,1)
    imshow(img)
    axis xy
    axis on
    xlabel('Red Intensity')
    ylabel('Blue Intensity')
    title('Valid Data')
    subtitle('Unknown values have been set to [255,255,255]')

    R = repmat(0:255,[256,1]);
    G = double(LUT(:,:,V));
    B = transpose(repmat(0:255,[256,1]));
    
    img = uint8(zeros([256,256,3]));
    img(:,:,1) = uint8(R) ;
    img(:,:,2) = uint8(G) ;
    img(:,:,3) = uint8(B) ;
    
    subplot(1,2,2)
    imshow(img)
    axis xy
    axis on
    xlabel('Red Intensity')
    ylabel('Blue Intensity')
    title('Interpolated Data')
        
    sgtitle(['Color LUT at Slice V=',num2str(V-1)])

    writeVideo(v,getframe(fig));

end

close(v)
