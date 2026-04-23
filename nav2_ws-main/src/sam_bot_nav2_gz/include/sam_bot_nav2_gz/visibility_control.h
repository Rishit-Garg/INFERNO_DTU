#ifndef SAM_BOT_NAV2_GZ__VISIBILITY_CONTROL_H_
#define SAM_BOT_NAV2_GZ__VISIBILITY_CONTROL_H_

// This logic was borrowed (then namespaced) from the examples on the gcc wiki:
//     https://gcc.gnu.org/wiki/Visibility

#if defined _WIN32 || defined __CYGWIN__
  #ifdef __GNUC__
    #define SAM_BOT_NAV2_GZ_EXPORT __attribute__ ((dllexport))
    #define SAM_BOT_NAV2_GZ_IMPORT __attribute__ ((dllimport))
  #else
    #define SAM_BOT_NAV2_GZ_EXPORT __declspec(dllexport)
    #define SAM_BOT_NAV2_GZ_IMPORT __declspec(dllimport)
  #endif
  #ifdef SAM_BOT_NAV2_GZ_BUILDING_DLL
    #define SAM_BOT_NAV2_GZ_PUBLIC SAM_BOT_NAV2_GZ_EXPORT
  #else
    #define SAM_BOT_NAV2_GZ_PUBLIC SAM_BOT_NAV2_GZ_IMPORT
  #endif
  #define SAM_BOT_NAV2_GZ_PUBLIC_TYPE SAM_BOT_NAV2_GZ_PUBLIC
  #define SAM_BOT_NAV2_GZ_LOCAL
#else
  #define SAM_BOT_NAV2_GZ_EXPORT __attribute__ ((visibility("default")))
  #define SAM_BOT_NAV2_GZ_IMPORT
  #if __GNUC__ >= 4
    #define SAM_BOT_NAV2_GZ_PUBLIC __attribute__ ((visibility("default")))
    #define SAM_BOT_NAV2_GZ_LOCAL  __attribute__ ((visibility("hidden")))
  #else
    #define SAM_BOT_NAV2_GZ_PUBLIC
    #define SAM_BOT_NAV2_GZ_LOCAL
  #endif
  #define SAM_BOT_NAV2_GZ_PUBLIC_TYPE
#endif

#endif  // SAM_BOT_NAV2_GZ__VISIBILITY_CONTROL_H_
