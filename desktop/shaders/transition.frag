#version 440
layout(location=0) in vec2 qt_TexCoord0;
layout(location=0) out vec4 fragColor;
layout(std140,binding=0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float progress;
    float kind;
    vec4 tint;
};
void main() {
    vec2 uv=qt_TexCoord0;
    float a=sin(progress*3.14159265);
    vec3 color=vec3(0.);
    if(kind<.5) {
        float n=fract(sin(dot(floor(uv*vec2(500.,300.)),vec2(12.9898,78.233))+floor(progress*30.))*43758.5453);
        color=mix(vec3(n),vec3(fract(uv.x*7.),fract(uv.x*7.+.33),fract(uv.x*7.+.66)),.5);
        a*=step(.15,fract(uv.y*15.+progress*6.));
    } else if(kind<1.5) {
        a=step(1.-a,abs(uv.y-.5)*2.);
    } else {
        color=tint.rgb;
        a=pow(a,2.);
    }
    fragColor=vec4(color*a,a)*qt_Opacity;
}
