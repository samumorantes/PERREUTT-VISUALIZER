#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec4 region;
    vec2 panelSize;
    vec2 backdropSize;
};
layout(binding = 1) uniform sampler2D source;
void main() {
    vec2 pixel = qt_TexCoord0 * panelSize;
    vec2 halfSize = panelSize*.5;
    vec2 d = abs(pixel-halfSize) - (halfSize-22.);
    float edge = length(max(d,0.)) + min(max(d.x,d.y),0.) - 22.;
    float alpha = 1.-smoothstep(-.7,.7,edge);
    vec2 uv = region.xy + qt_TexCoord0 * region.zw;
    // A shallow lens around the panel edge, followed by a wide blur.
    uv += (qt_TexCoord0-.5)*exp(-abs(edge)/13.)*.018;
    vec2 stepUV = vec2(10.) / max(backdropSize,vec2(1.));
    vec3 blurred = texture(source,clamp(uv,0.,1.)).rgb * .2;
    for (int i=0;i<12;i++) {
        float angle = float(i)*.52359878;
        vec2 offset = vec2(cos(angle),sin(angle))*stepUV;
        blurred += texture(source,clamp(uv+offset,0.,1.)).rgb * (.8/12.);
    }
    float luma = dot(blurred,vec3(.2126,.7152,.0722));
    blurred = mix(vec3(luma),blurred,1.3);
    vec3 rgb = mix(blurred,vec3(.045,.055,.085),.72);
    rgb += vec3(.065,.075,.10)*pow(1.-qt_TexCoord0.y,3.);
    float rim = 1.-smoothstep(.6,1.9,abs(edge));
    rgb += rim * mix(vec3(.08),vec3(.35,.4,.47),1.-qt_TexCoord0.y);
    fragColor = vec4(rgb*alpha,alpha)*qt_Opacity;
}
