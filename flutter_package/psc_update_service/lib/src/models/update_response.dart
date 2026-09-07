class PscUpdateInfo {
  final bool updateAvailable;
  final bool updateRequired;
  final String? latestVersion;
  final int? latestBuild;
  final String? minimumSupportedVersion;
  final String? title;
  final String? message;
  final List<String> releaseNotes;
  final String? updateUrl;

  const PscUpdateInfo({
    required this.updateAvailable,
    required this.updateRequired,
    this.latestVersion,
    this.latestBuild,
    this.minimumSupportedVersion,
    this.title,
    this.message,
    this.releaseNotes = const [],
    this.updateUrl,
  });

  /// Used when the backend is unreachable / offline - never blocks the app.
  factory PscUpdateInfo.none() => const PscUpdateInfo(
        updateAvailable: false,
        updateRequired: false,
      );

  factory PscUpdateInfo.fromJson(Map<String, dynamic> json) {
    return PscUpdateInfo(
      updateAvailable: json['update_available'] as bool? ?? false,
      updateRequired: json['update_required'] as bool? ?? false,
      latestVersion: json['latest_version'] as String?,
      latestBuild: json['latest_build'] as int?,
      minimumSupportedVersion: json['minimum_supported_version'] as String?,
      title: json['title'] as String?,
      message: json['message'] as String?,
      releaseNotes: (json['release_notes'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      updateUrl: json['update_url'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'update_available': updateAvailable,
        'update_required': updateRequired,
        'latest_version': latestVersion,
        'latest_build': latestBuild,
        'minimum_supported_version': minimumSupportedVersion,
        'title': title,
        'message': message,
        'release_notes': releaseNotes,
        'update_url': updateUrl,
      };
}
