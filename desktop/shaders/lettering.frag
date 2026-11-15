#version 440
layout(location=0) in vec2 qt_TexCoord0;
layout(location=0) out vec4 fragColor;
layout(std140,binding=0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 pixelSize;
    float stroke;
    float shadow;
    vec4 edgeColor;
};
layout(binding=1) uniform sampler2D source;
void main() {
    vec2 uv=qt_TexCoord0;
    vec4 text=texture(source,uv);
    float edge=text.a, shade=0.;
    for(int i=0;i<8;i++) {
        float angle=float(i)*.785398;
        vec2 d=vec2(cos(angle),sin(angle));
        edge=max(edge,texture(source,uv+d*pixelSize*stroke).a);
        shade+=texture(source,uv-pixelSize*(vec2(3.,5.)+d*4.)).a/8.;
    }
    float a=max(edge,shade*shadow);
    fragColor=vec4(text.rgb+edgeColor.rgb*max(0.,edge-text.a),a)*qt_Opacity;
}
