#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float seconds;
    float pulseStart;
    float pulseDuration;
    float strength;
    float chill;
    float style;
    vec4 pulseColor;
    vec4 colorA;
    vec4 colorB;
    vec4 colorC;
    vec4 colorD;
    vec4 colorE;
    float trails;
};
vec3 fluid(vec2 uv, float seconds) {
    vec2 p = (uv-.5)*3.;
    float t = seconds*.18;
    float f = sin(p.x*2. + sin(p.y*2. + t))*.5+.5;
    if (style > .5 && style < 1.5) f = sin(atan(p.y,p.x)*3. + length(p)*4. - t)*.5+.5;
    if (style > 1.5 && style < 2.5) f = (sin(p.x*3.+t)+sin(p.y*4.-t)+sin(length(p)*4.-t))*.1667+.5;
    if (style > 2.5) f = pow(max(0.,sin(p.x*2.+sin(p.y+t)+t)),2.)*(.4+.6*uv.y);
    float band = f * 4.;
    vec3 rgb = band < 1. ? mix(colorA.rgb,colorB.rgb,smoothstep(0.,1.,band)) :
               band < 2. ? mix(colorB.rgb,colorC.rgb,smoothstep(1.,2.,band)) :
               band < 3. ? mix(colorC.rgb,colorD.rgb,smoothstep(2.,3.,band)) :
                          mix(colorD.rgb,colorE.rgb,smoothstep(3.,4.,band));
    return rgb * (.85 + .15*sin(p.x+p.y+t));
}
void main() {
    vec2 uv = qt_TexCoord0;
    float age = seconds - pulseStart;
    float hold = min(.12, pulseDuration * .22);
    float u = clamp((age - hold) / max(.01, pulseDuration - hold), 0., 1.);
    float envelope = (age >= 0. && age < pulseDuration) ? (exp(-1.2*u)-exp(-1.2))/(1.-exp(-1.2)) : 0.;
    vec3 rgb = pulseColor.rgb * envelope * strength;
    if (chill > .5) {
        rgb = fluid(uv,seconds);
        if (trails > .5) rgb = rgb*.5 + fluid(uv,seconds-.65)*.3 + fluid(uv,seconds-1.3)*.2;
        rgb = min(vec3(1.), rgb * (1. + envelope*.25*strength));
    }
    fragColor = vec4(rgb,1.) * qt_Opacity;
}
