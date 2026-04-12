::GimConv.exe font1-1.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-1.gim
::GimConv.exe font1-2.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-2.gim
::GimConv.exe font1-3.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-3.gim
::GimConv.exe font1-4.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-4.gim
::GimConv.exe font1-5.png --image_format index4 --pixel_order normal --palette_format rgba4444 -o font1-5.gim

gimconv.exe -ndx font1-1.png -N -o font1-1.gim --filter_script2 ReducePalette
gimconv.exe -ndx font1-2.png -N -o font1-2.gim --filter_script2 ReducePalette
gimconv.exe -ndx font1-3.png -N -o font1-3.gim --filter_script2 ReducePalette
gimconv.exe -ndx font1-4.png -N -o font1-4.gim --filter_script2 ReducePalette
gimconv.exe -ndx font1-5.png -N -o font1-5.gim --filter_script2 ReducePalette

pause