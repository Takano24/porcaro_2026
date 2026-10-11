# ヒステリシスの比較（hys_loops.py）

## tm_A：DF 三角波のループ（tri0 / tri1）

```
                            dA_deg       dP_kPa        rmse      
tri                              0     1      0     1     0     1
pmodel       hys                                                 
measured_raw play_w10_cp15    -1.7  -1.6   -3.4 -12.8  12.5   9.7
             play_w10_cp7.5   -1.3  -1.2   -3.7  -9.1  13.0  10.0
             play_w20_cp15    -5.9  -3.6   -8.5 -36.1  11.8   9.0
             play_w20_cp7.5   -3.1  -2.4  -12.6  -1.3  12.5   9.6
             play_w40_cp15    -8.1  -4.6  -40.7 -11.1  11.4   8.5
             play_w40_cp30   -18.2  -9.3  -19.4 -35.9  10.9   9.4
             play_w40_cp7.5   -4.3  -3.1  -22.4 -26.3  12.2   9.2
             play_w80_cp15    -7.0  -5.4  -50.0 -32.2  11.0   8.4
             play_w80_cp30   -21.3 -10.8  -90.4 -66.5  11.3  10.5
             relay            -0.8  -0.8   -3.6  -1.8  12.1   9.3
measured_v2  relay           -13.1 -14.2  -98.6 -92.9  11.4   8.3
orificeV2    play_w40_cp15   -13.8 -13.8  -93.3 -93.3  11.6   9.5
             relay           -13.8 -13.8  -94.5 -94.5  11.9   9.8
real         real             -9.4  -4.0  -80.0 -52.6   0.0   0.0
```

## 手首角（全動作）

```
pmodel                measured_raw                                                                                                                                        measured_v2        orificeV2                    
hys               play_w10-40_cp15 play_w10_cp15 play_w10_cp7.5 play_w20_cp15 play_w20_cp7.5 play_w40_cp15 play_w40_cp30 play_w40_cp7.5 play_w80_cp15 play_w80_cp30 relay       relay play_w10-40_cp15 play_w40_cp15 relay
motion                                                                                                                                                                                                                    
tm_A_quasistatic               NaN           7.7            8.0           7.3            7.7           6.9           7.1            7.5           6.8           7.5   7.4         6.9              NaN           7.3   7.5
tm_B_steps                     6.1           NaN            NaN           NaN            NaN           5.1           NaN            NaN           NaN           NaN   6.0         NaN              4.9           4.9   4.8
tm_C_sine                      9.3           NaN            NaN           NaN            NaN           9.3           NaN            NaN           NaN           NaN   8.7         NaN             10.1           9.9  10.1
tm_D_antagonist                5.6           NaN            NaN           NaN            NaN           5.8           NaN            NaN           NaN           NaN   5.6         NaN              7.1           7.2   7.0
tm_E_dbl160_seed2              8.0           NaN            NaN           NaN            NaN           8.4           NaN            NaN           NaN           NaN   7.9         NaN              9.2           9.5   9.2
tm_E_dbl160_seed3              9.8           NaN            NaN           NaN            NaN          10.1           NaN            NaN           NaN           NaN  10.0         NaN             11.4          11.8  11.1
```
