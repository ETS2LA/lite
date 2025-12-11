#define SUBSTANCE_SIZE 25
#define stringsize  64


// MARK: SCSTrailer struct
typedef struct SCSTrailer {
    // Constant bool
	struct {
		bool wheelSteerable[16];
		bool wheelSimulated[16];
		bool wheelPowered[16];
		bool wheelLiftable[16];
	} con_b;

    // Common bool
	struct {
		bool wheelOnGround[16];
		bool attached;
	} com_b;

	char buffer_b[3];

    // Common unsigned int
	struct {
		unsigned int wheelSubstance[16];
	} com_ui;

    // Constant unsigned int
	struct {
		unsigned int wheelCount;
	} con_ui;

    // Common float
	struct {
		float cargoDamage;
		float wearChassis;
		float wearWheels;
		float wearBody;
		float wheelSuspDeflection[16];
		float wheelVelocity[16];
		float wheelSteering[16];
		float wheelRotation[16];
		float wheelLift[16];
		float wheelLiftOffset[16];
	} com_f;

	/// Constant float
	struct {
		float wheelRadius[16];
	} con_f;

    // Common float vector
	struct {
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
	struct {
		float hookPositionX;
		float hookPositionY;
		float hookPositionZ;
		float wheelPositionX[16];
		float wheelPositionY[16];
		float wheelPositionZ[16];
	} con_fv;

    char buffer_fv[4];

    // Common double placement
	struct {
		double worldX;
		double worldY;
		double worldZ;
		double rotationX;
		double rotationY;
		double rotationZ;
	} com_dp;

    // Constant string
	struct {
		char id[stringsize];
		char cargoAcessoryId[stringsize];
		char bodyType[stringsize];
		char brandId[stringsize];
		char brand[stringsize];
		char name[stringsize];
		char chainType[stringsize];
		char licensePlate[stringsize];
		char licensePlateCountry[stringsize];
		char licensePlateCountryId[stringsize];
	} con_s;
};


// MARK: SCSTelemetry struct
typedef struct SCSTelemetry {

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
	struct {
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
	struct {
		// In game time in minutes
		unsigned int time_abs;
	} com_ui;

	// Configuration unsigned int
	struct {
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
	struct {
		unsigned int shifterSlot;
		unsigned int retarderBrake;
		unsigned int lightsAuxFront;
		unsigned int lightsAuxRoof;
		unsigned int truck_wheelSubstance[16];
		unsigned int hshifterPosition[32];
		unsigned int hshifterBitmask[32];
	} truck_ui;

    // Gameplay unsigned int
	struct {
		unsigned int jobDeliveredDeliveryTime;
		unsigned int jobStartingTime;
		unsigned int jobFinishedTime;
	} gameplay_ui;

	char buffer_ui[48];

    // Common int
	struct {
		int restStop;
	} com_i;

    // Truck int
	struct {
		int gear;
		int gearDashboard;
		int hshifterResulting[32];
	} truck_i;

    // Gameplay int
	struct {
		int jobDeliveredEarnedXp;
	} gameplay_i;

	char buffer_i[56];

    // Common float
	struct {
		float scale;
	} com_f;

    // Configuration float
	struct {
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
		float truckWheelRadius[16];
		float gearRatiosForward[24];
		float gearRatiosReverse[8];
		float unitMass;
	} config_f;

    // Truck float
	struct {
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
		float truck_wheelSuspDeflection[16];
		float truck_wheelVelocity[16];
		float truck_wheelSteering[16];
		float truck_wheelRotation[16];
		float truck_wheelLift[16];
		float truck_wheelLiftOffset[16];
	} truck_f;

    // Gameplay float
	struct {
		float jobDeliveredCargoDamage;
		float jobDeliveredDistanceKm;
		float refuelAmount;
	} gameplay_f;

    // Job float
	struct {
		float cargoDamage;
	} job_f;

	char buffer_f[28];

    // Configuration bool
	struct {
		bool truckWheelSteerable[16];
		bool truckWheelSimulated[16];
		bool truckWheelPowered[16];
		bool truckWheelLiftable[16];

		bool isCargoLoaded;
		bool specialJob;
	} config_b;

    // Truck bool
	struct {
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
		bool truck_wheelOnGround[16];
		bool shifterToggle[2];
		bool differentialLock;
		bool liftAxle;
		bool liftAxleIndicator;
		bool trailerLiftAxle;
		bool trailerLiftAxleIndicator;
	} truck_b;

    // Gameplay bool
	struct {
		bool jobDeliveredAutoparkUsed;
		bool jobDeliveredAutoloadUsed;
	} gameplay_b;

	char buffer_b[25];

    // Configuration float vector
	struct {
		float cabinPositionX;
		float cabinPositionY;
		float cabinPositionZ;
		float headPositionX;
		float headPositionY;
		float headPositionZ;
		float truckHookPositionX;
		float truckHookPositionY;
		float truckHookPositionZ;
		float truckWheelPositionX[16];
		float truckWheelPositionY[16];
		float truckWheelPositionZ[16];
	} config_fv;

    // Truck float velocity
	struct {
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
	struct {
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
	struct {
		double coordinateX;
		double coordinateY;
		double coordinateZ;
		double rotationX;
		double rotationY;
		double rotationZ;
	} truck_dp;

	char buffer_dp[52];

    // Configuration string
	struct {
		char truckBrandId[stringsize];
		char truckBrand[stringsize];
		char truckId[stringsize];

		char truckName[stringsize];
		char cargoId[stringsize];
		char cargo[stringsize];
		char cityDstId[stringsize];
		char cityDst[stringsize];
		char compDstId[stringsize];
		char compDst[stringsize];
		char citySrcId[stringsize];
		char citySrc[stringsize];
		char compSrcId[stringsize];
		char compSrc[stringsize];
		char shifterType[16];

		char truckLicensePlate[stringsize];
		char truckLicensePlateCountryId[stringsize];
		char truckLicensePlateCountry[stringsize];

		char jobMarket[32];
	} config_s;

    // Gameplay string
	struct {
		char fineOffence[32];
		char ferrySourceName[stringsize];
		char ferryTargetName[stringsize];
		char ferrySourceId[stringsize];
		char ferryTargetId[stringsize];
		char trainSourceName[stringsize];
		char trainTargetName[stringsize];
		char trainSourceId[stringsize];
		char trainTargetId[stringsize];
	} gameplay_s;

	char buffer_s[20];

    // Configuration unsigned long long
	struct {
		unsigned long long jobIncome;
	} config_ull;

	char buffer_ull[192];

    // Gameplay long long
	struct {
		long long jobCancelledPenalty;
		long long jobDeliveredRevenue;
		long long fineAmount;
		long long tollgatePayAmount;
		long long ferryPayAmount;
		long long trainPayAmount;
	} gameplay_ll;

	char buffer_ll[52];

    // Special bool
	struct {
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
	struct {
		char substance[SUBSTANCE_SIZE][stringsize];
	} substances;

    // Trailer struct
	struct {
		SCSTrailer trailer[10];
	} trailer;

};