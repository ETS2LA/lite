#pragma once
#define NOMINMAX

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>
#include <windows.h>

#define SUBSTANCE_SIZE 25
#define STRINGSIZE  64
#define WHEEL_MAX 16


// MARK: TelemetryDataTrailer struct
struct TelemetryDataTrailer {
    // Constant bool
    struct ConstantBool {
        bool wheelSteerable[WHEEL_MAX];
        bool wheelSimulated[WHEEL_MAX];
        bool wheelPowered[WHEEL_MAX];
        bool wheelLiftable[WHEEL_MAX];
    } con_b;

    // Common bool
    struct CommonBool {
        bool wheelOnGround[WHEEL_MAX];
        bool attached;
    } com_b;

    char buffer_b[3];

    // Common unsigned int
    struct CommonUnsignedInt {
        unsigned int wheelSubstance[WHEEL_MAX];
    } com_ui;

    // Constant unsigned int
    struct ConstantUnsignedInt {
        unsigned int wheelCount;
    } con_ui;

    // Common float
    struct CommonFloat {
        float cargoDamage;
        float wearChassis;
        float wearWheels;
        float wearBody;
        float wheelSuspDeflection[WHEEL_MAX];
        float wheelVelocity[WHEEL_MAX];
        float wheelSteering[WHEEL_MAX];
        float wheelRotation[WHEEL_MAX];
        float wheelLift[WHEEL_MAX];
        float wheelLiftOffset[WHEEL_MAX];
    } com_f;

    /// Constant float
    struct ConstantFloat {
        float wheelRadius[WHEEL_MAX];
    } con_f;

    // Common float vector
    struct CommonFloatVector {
        float linearVelocityX;
        float linearVelocityY;
        float linearVelocityZ;
        float angularVelocityX;
        float angularVelocityY;
        float angularVelocityZ;
        float linearAccelerationX;
        float linearAccelerationY;
        float linearAccelerationZ;
        float angularAccelerationX;
        float angularAccelerationY;
        float angularAccelerationZ;
    } com_fv;

    // Constant float vector
    struct ConstantFloatVector {
        float hookPositionX;
        float hookPositionY;
        float hookPositionZ;
        float wheelPositionX[WHEEL_MAX];
        float wheelPositionY[WHEEL_MAX];
        float wheelPositionZ[WHEEL_MAX];
    } con_fv;

    char buffer_fv[4];

    // Common double placement
    struct CommonDoublePlacement {
        double worldX;
        double worldY;
        double worldZ;
        double rotationX;
        double rotationY;
        double rotationZ;
    } com_dp;

    // Constant string
    struct ConstantString {
        char id[STRINGSIZE];
        char cargoAcessoryId[STRINGSIZE];
        char bodyType[STRINGSIZE];
        char brandId[STRINGSIZE];
        char brand[STRINGSIZE];
        char name[STRINGSIZE];
        char chainType[STRINGSIZE];
        char licensePlate[STRINGSIZE];
        char licensePlateCountry[STRINGSIZE];
        char licensePlateCountryId[STRINGSIZE];
    } con_s;
};


// MARK: TelemetryData struct
struct TelemetryData {

    // Display if game / sdk runs
    bool sdkActive;
    char placeHolder[3];

    // Check if the game and the telemetry is paused
    bool paused;
    char placeHolder2[3];

    // Not the game time, only a timestamp. Used to update the values on the other site of the shared memory
    unsigned long long time;
    unsigned long long simulatedTime;
    unsigned long long renderTime;
    long long multiplayerTimeOffset;


    // Game independent unsigned int
    struct ScsValuesUnsignedInt {
        // Telemetry Plugin Version
        unsigned int telemetry_plugin_revision;
        // Game major version
        unsigned int version_major;
        // Game minor version
        unsigned int version_minor;
        // Game identifier
        unsigned int game; // actually 0 for unknown,1 for ets2 and 2 for ats
        // Game telemetry version major
        unsigned int telemetry_version_game_major;
        // Game telemetry version minor
        unsigned int telemetry_version_game_minor;
    } scs_values;

    // Common unsigned int
    struct CommonUnsignedInt {
        // In game time in minutes
        unsigned int time_abs;
    } com_ui;

    // Configuration unsigned int
    struct ConfigurationUnsignedInt {
        unsigned int gears;
        unsigned int gears_reverse;
        unsigned int retarderStepCount;
        unsigned int truckWheelCount;
        unsigned int selectorCount;
        unsigned int time_abs_delivery;
        unsigned int maxTrailerCount;
        unsigned int unitCount;
        unsigned int plannedDistanceKm;
    } config_ui;

    // Truck unsigned int
    struct TruckUnsignedInt {
        unsigned int shifterSlot;
        unsigned int retarderBrake;
        unsigned int lightsAuxFront;
        unsigned int lightsAuxRoof;
        unsigned int truck_wheelSubstance[WHEEL_MAX];
        unsigned int hshifterPosition[32];
        unsigned int hshifterBitmask[32];
    } truck_ui;

    // Gameplay unsigned int
    struct GameplayUnsignedInt {
        unsigned int jobDeliveredDeliveryTime;
        unsigned int jobStartingTime;
        unsigned int jobFinishedTime;
    } gameplay_ui;

    char buffer_ui[48];

    // Common int
    struct CommonInt {
        int restStop;
    } com_i;

    // Truck int
    struct TruckInt {
        int gear;
        int gearDashboard;
        int hshifterResulting[32];
    } truck_i;

    // Gameplay int
    struct GameplayInt {
        int jobDeliveredEarnedXp;
    } gameplay_i;

    char buffer_i[56];

    // Common float
    struct CommonFloat {
        float scale;
    } com_f;

    // Configuration float
    struct ConfigurationFloat {
        float fuelCapacity;
        float fuelWarningFactor;
        float adblueCapacity;
        float adblueWarningFactor;
        float airPressureWarning;
        float airPressurEmergency;
        float oilPressureWarning;
        float waterTemperatureWarning;
        float batteryVoltageWarning;
        float engineRpmMax;
        float gearDifferential;
        float cargoMass;
        float truckWheelRadius[WHEEL_MAX];
        float gearRatiosForward[24];
        float gearRatiosReverse[8];
        float unitMass;
    } config_f;

    // Truck float
    struct TruckFloat {
        float speed;
        float engineRpm;
        float userSteer;
        float userThrottle;
        float userBrake;
        float userClutch;
        float gameSteer;
        float gameThrottle;
        float gameBrake;
        float gameClutch;
        float cruiseControlSpeed;
        float airPressure;
        float brakeTemperature;
        float fuel;
        float fuelAvgConsumption;
        float fuelRange;
        float adblue;
        float oilPressure;
        float oilTemperature;
        float waterTemperature;
        float batteryVoltage;
        float lightsDashboard;
        float wearEngine;
        float wearTransmission;
        float wearCabin;
        float wearChassis;
        float wearWheels;
        float truckOdometer;
        float routeDistance;
        float routeTime;
        float speedLimit;
        float truck_wheelSuspDeflection[WHEEL_MAX];
        float truck_wheelVelocity[WHEEL_MAX];
        float truck_wheelSteering[WHEEL_MAX];
        float truck_wheelRotation[WHEEL_MAX];
        float truck_wheelLift[WHEEL_MAX];
        float truck_wheelLiftOffset[WHEEL_MAX];
    } truck_f;

    // Gameplay float
    struct GameplayFloat {
        float jobDeliveredCargoDamage;
        float jobDeliveredDistanceKm;
        float refuelAmount;
    } gameplay_f;

    // Job float
    struct JobFloat {
        float cargoDamage;
    } job_f;

    char buffer_f[28];

    // Configuration bool
    struct ConfigurationBool {
        bool truckWheelSteerable[WHEEL_MAX];
        bool truckWheelSimulated[WHEEL_MAX];
        bool truckWheelPowered[WHEEL_MAX];
        bool truckWheelLiftable[WHEEL_MAX];

        bool isCargoLoaded;
        bool specialJob;
    } config_b;

    // Truck bool
    struct TruckBool {
        bool parkBrake;
        bool motorBrake;
        bool airPressureWarning;
        bool airPressureEmergency;
        bool fuelWarning;
        bool adblueWarning;
        bool oilPressureWarning;
        bool waterTemperatureWarning;
        bool batteryVoltageWarning;
        bool electricEnabled;
        bool engineEnabled;
        bool wipers;
        bool blinkerLeftActive;
        bool blinkerRightActive;
        bool blinkerLeftOn;
        bool blinkerRightOn;
        bool lightsParking;
        bool lightsBeamLow;
        bool lightsBeamHigh;
        bool lightsBeacon;
        bool lightsBrake;
        bool lightsReverse;
        bool lightsHazard;
        bool cruiseControl; // special field not a sdk field
        bool truck_wheelOnGround[WHEEL_MAX];
        bool shifterToggle[2];
        bool differentialLock;
        bool liftAxle;
        bool liftAxleIndicator;
        bool trailerLiftAxle;
        bool trailerLiftAxleIndicator;
    } truck_b;

    // Gameplay bool
    struct GameplayBool {
        bool jobDeliveredAutoparkUsed;
        bool jobDeliveredAutoloadUsed;
    } gameplay_b;

    char buffer_b[25];

    // Configuration float vector
    struct ConfigurationFloatVector {
        float cabinPositionX;
        float cabinPositionY;
        float cabinPositionZ;
        float headPositionX;
        float headPositionY;
        float headPositionZ;
        float truckHookPositionX;
        float truckHookPositionY;
        float truckHookPositionZ;
        float truckWheelPositionX[WHEEL_MAX];
        float truckWheelPositionY[WHEEL_MAX];
        float truckWheelPositionZ[WHEEL_MAX];
    } config_fv;

    // Truck float velocity
    struct TruckFloatVelocity {
        float lv_accelerationX;
        float lv_accelerationY;
        float lv_accelerationZ;
        float av_accelerationX;
        float av_accelerationY;
        float av_accelerationZ;
        float accelerationX;
        float accelerationY;
        float accelerationZ;
        float aa_accelerationX;
        float aa_accelerationY;
        float aa_accelerationZ;
        float cabinAVX;
        float cabinAVY;
        float cabinAVZ;
        float cabinAAX;
        float cabinAAY;
        float cabinAAZ;
    } truck_fv;

    char buffer_fv[60];

    // Truck float placement
    struct TruckFloatPlacement {
        float cabinOffsetX;
        float cabinOffsetY;
        float cabinOffsetZ;
        float cabinOffsetrotationX;
        float cabinOffsetrotationY;
        float cabinOffsetrotationZ;
        float headOffsetX;
        float headOffsetY;
        float headOffsetZ;
        float headOffsetrotationX;
        float headOffsetrotationY;
        float headOffsetrotationZ;
    } truck_fp;

    char buffer_fp[152];

    // Truck double placement
    struct TruckDoublePlacement {
        double coordinateX;
        double coordinateY;
        double coordinateZ;
        double rotationX;
        double rotationY;
        double rotationZ;
    } truck_dp;

    char buffer_dp[52];

    // Configuration string
    struct ConfigurationString {
        char truckBrandId[STRINGSIZE];
        char truckBrand[STRINGSIZE];
        char truckId[STRINGSIZE];

        char truckName[STRINGSIZE];
        char cargoId[STRINGSIZE];
        char cargo[STRINGSIZE];
        char cityDstId[STRINGSIZE];
        char cityDst[STRINGSIZE];
        char compDstId[STRINGSIZE];
        char compDst[STRINGSIZE];
        char citySrcId[STRINGSIZE];
        char citySrc[STRINGSIZE];
        char compSrcId[STRINGSIZE];
        char compSrc[STRINGSIZE];
        char shifterType[16];

        char truckLicensePlate[STRINGSIZE];
        char truckLicensePlateCountryId[STRINGSIZE];
        char truckLicensePlateCountry[STRINGSIZE];

        char jobMarket[32];
    } config_s;

    // Gameplay string
    struct GameplayString {
        char fineOffence[32];
        char ferrySourceName[STRINGSIZE];
        char ferryTargetName[STRINGSIZE];
        char ferrySourceId[STRINGSIZE];
        char ferryTargetId[STRINGSIZE];
        char trainSourceName[STRINGSIZE];
        char trainTargetName[STRINGSIZE];
        char trainSourceId[STRINGSIZE];
        char trainTargetId[STRINGSIZE];
    } gameplay_s;

    char buffer_s[20];

    // Configuration unsigned long long
    struct ConfigurationUnsignedLongLong {
        unsigned long long jobIncome;
    } config_ull;

    char buffer_ull[192];

    // Gameplay long long
    struct GameplayLongLong {
        long long jobCancelledPenalty;
        long long jobDeliveredRevenue;
        long long fineAmount;
        long long tollgatePayAmount;
        long long ferryPayAmount;
        long long trainPayAmount;
    } gameplay_ll;

    char buffer_ll[52];

    // Special bool
    struct SpecialBool {
        bool onJob;
        bool jobFinished;
        bool jobCancelled;
        bool jobDelivered;
        bool fined;
        bool tollgate;
        bool ferry;
        bool train;
        bool refuel;
        bool refuelPayed;
    } special_b;

    char buffer_special[90];

    // Substance string
    struct SubstanceString {
        char substance[SUBSTANCE_SIZE][STRINGSIZE];
    } substances;

    // Trailer struct
    struct Trailer {
        TelemetryDataTrailer trailer[10];
    } trailer;

};


// MARK: SCSTelemetry class
class SCSTelemetry {
public:
    SCSTelemetry();
    SCSTelemetry(const std::wstring &mapName, std::size_t mapSize = sizeof(TelemetryData));
    SCSTelemetry(const SCSTelemetry &) = delete;
    SCSTelemetry &operator=(const SCSTelemetry &) = delete;
    SCSTelemetry(SCSTelemetry &&other) noexcept;
    SCSTelemetry &operator=(SCSTelemetry &&other) noexcept;
    ~SCSTelemetry();

    bool open(const std::wstring &mapName = L"Local\\SCSTelemetry", std::size_t mapSize = sizeof(TelemetryData));
    void close();

    bool hooked() const { return hooked_; }
    std::size_t size() const { return size_; }

    TelemetryData *data();
    const TelemetryData *data() const;

private:
    bool ensure_open() const;

    HANDLE mapHandle_;
    void *view_;
    std::size_t size_;
    bool hooked_;
    std::wstring mapName_;
    std::size_t mapSize_;
    TelemetryData fallback_{};
};