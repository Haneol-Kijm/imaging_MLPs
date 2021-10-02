import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import init
import torch.nn.init as init
import numpy as np

import einops
from einops.layers.torch import Rearrange
from einops import rearrange


class PatchEmbeddings(nn.Module):

    def __init__(
        self,
        patch_size: int,
        embed_dim: int,
        channels: int 
    ):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Conv2d(
                in_channels=channels,
                out_channels=embed_dim,
                kernel_size=patch_size,
                stride=patch_size
            ),
            Rearrange("b c h w -> b h w c")
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.proj(x)
    

class FinalPatchExpand(nn.Module):
    def __init__(self, dim_scale, channel_dim, img_channels, norm_layer=nn.LayerNorm):
        super().__init__()
        self.dim_scale = dim_scale
        self.expand = nn.Linear(channel_dim, dim_scale**2* channel_dim, bias=False)
        self.output_dim = channel_dim 
        self.norm = norm_layer(channel_dim)
        self.output = nn.Conv2d(in_channels=channel_dim,out_channels=img_channels ,kernel_size=1,bias=False)

    def forward(self, x):
        """
        x: B, H, W, C
        """

        x = self.expand(x)
        B, H, W, C = x.shape

        x = rearrange(x, 'b h w (p1 p2 c)-> b (h p1) (w p2) c', p1=self.dim_scale, p2=self.dim_scale, c=C//(self.dim_scale**2))
        x = x.view(B,-1,self.output_dim)
        x= self.norm(x)
        
        x = x.view(B,H*self.dim_scale, W*self.dim_scale,-1)
        x = x.permute(0,3,1,2)
        x = self.output(x)

        return x
    

class MLPBlock(nn.Module):

    def __init__(self, input_dim: int, hidden_dim: int):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, input_dim)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class Mixer(nn.Module):

    def __init__(
        self,
        num_patches: int,
        num_channels: int
    ):
        super().__init__()
        self.token_mixing = nn.Sequential(
            nn.LayerNorm(num_channels),
            Rearrange("b h w c -> b c w h"),
            MLPBlock(num_patches, num_patches),
            Rearrange("b c w h -> b c h w"),
            MLPBlock(num_patches, num_patches),
            Rearrange("b c h w -> b h w c"),
        )
        self.channel_mixing = nn.Sequential(
            nn.LayerNorm(num_channels),
            MLPBlock(num_channels, num_channels)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.token_mixing(x)
        x = x + self.channel_mixing(x)
        return x


class Unet_Mixer_p1(nn.Module):

    def __init__(
        self,
        img_size: int = 256,
        img_channels: int = 1,
        patch_size: int = 1,
        embed_dim: int = 107,     
    ):    
        super().__init__()
        
        #mixer blocks
        self.mixer1= Mixer( img_size//patch_size, embed_dim)
        self.mixer2= Mixer( img_size//patch_size, embed_dim)
        self.mixer3= Mixer( img_size//patch_size, embed_dim)
        self.mixer4= Mixer( img_size//patch_size, embed_dim)
        
        self.mixer5= Mixer( img_size//patch_size, embed_dim)
        self.mixer6= Mixer( img_size//patch_size, embed_dim)
        self.mixer7= Mixer( img_size//patch_size, embed_dim)
        self.mixer8= Mixer( img_size//patch_size, embed_dim)
        
        self.mixer9 = Mixer( img_size//patch_size, embed_dim)
        self.mixer10= Mixer( img_size//patch_size, embed_dim)
        self.mixer11= Mixer( img_size//patch_size, embed_dim)
        self.mixer12= Mixer( img_size//patch_size, embed_dim)
        
        #self.mixer13 = Mixer( img_size//patch_size, embed_dim)
        #self.mixer14= Mixer( img_size//patch_size, embed_dim)
        #self.mixer15= Mixer( img_size//patch_size, embed_dim)
        #self.mixer16= Mixer( img_size//patch_size, embed_dim)
        
        
        
        #encode
        self.patch_embed = PatchEmbeddings(patch_size, embed_dim, img_channels)

        self.final_expand = FinalPatchExpand(patch_size, embed_dim, img_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
                
        x = self.patch_embed(x)
        
        x = self.mixer1(x)
        x = self.mixer2(x)
        x = self.mixer3(x)
        x = self.mixer4(x)
        x = self.mixer5(x)
        x = self.mixer6(x)
        x = self.mixer7(x)
        x = self.mixer8(x)
        x = self.mixer9(x)
        x = self.mixer10(x)
        x = self.mixer11(x)
        x = self.mixer12(x)
        #x = self.mixer13(x)
        #x = self.mixer14(x)
        #x = self.mixer15(x)
        #x = self.mixer16(x)
        
        x = self.final_expand(x)
        return x        