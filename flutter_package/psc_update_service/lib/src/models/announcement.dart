class PscAnnouncement {
  final String id;
  final String title;
  final String message;

  const PscAnnouncement({
    required this.id,
    required this.title,
    required this.message,
  });

  factory PscAnnouncement.fromJson(Map<String, dynamic> json) {
    return PscAnnouncement(
      id: json['id'] as String,
      title: json['title'] as String? ?? '',
      message: json['message'] as String? ?? '',
    );
  }
}
