#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float curvature;
    float scan;
    float mask;
    float vignette;
    float grain;
    float seconds;
    vec2 resolution;
    float flicker;
    float refresh;
    float tilt;
};
layout(binding = 1) uniform sampler2D source;
void main() {
    vec2 p = qt_TexCoord0 * 2. - 1.;
    // Boundary-preserving barrel warp: each axis remains monotonic on [-1,1]
    // for curvature <= .2. Never sample outside the scene or smear edge pixels.
    vec2 q = p * (1. + curvature * (1. - p*p) * p.yx*p.yx);
    // Tiny internal sway, also zero at each boundary: the glass stays filled.
    q += tilt*.004*sin(seconds*.8)*(1.-p*p)*vec2(p.y,-p.x);
    vec2 uv = q*.5+.5;
    vec3 rgb = texture(source,uv).rgb;
    // Phosphor pitch belongs to output pixels, independently of the lens.
    rgb *= 1. - scan*.23*(.5+.5*sin(qt_TexCoord0.y*resolution.y*3.14159265));
    float col = mod(floor(qt_TexCoord0.x*resolution.x), 3.);
    vec3 phosphor = col < 1. ? vec3(1.,.75,.75) : col < 2. ? vec3(.75,1.,.75) : vec3(.75,.75,1.);
    rgb *= mix(vec3(1.),phosphor,mask);
    rgb *= 1. - vignette*.48*smoothstep(.74,1.,length(p)/1.41421356);
    float noise = fract(sin(dot(uv*resolution,vec2(12.9898,78.233)) + floor(seconds*24.))*43758.5453)-.5;
    rgb = max(vec3(0.),rgb + noise*grain*.045);
    rgb *= 1.-flicker*.025*(.5+.5*sin(seconds*43.));
    float band = 1.-smoothstep(0.,.085,abs(uv.y-fract(seconds/8.)));
    rgb += refresh*band*.045;
    fragColor = vec4(rgb,1.) * qt_Opacity;
}
